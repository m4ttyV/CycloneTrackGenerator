"""Integration tests for catalog and ID filters without a live PostgreSQL server."""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import functions
from engine.catalog import list_cyclones
from engine.database import load_source_rows


class StubCursor:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []
        self.closed = False

    def execute(self, query, params):
        self.calls.append((query, params))

    def fetchall(self):
        return next(self.responses)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True


class StubConnection:
    def __init__(self, responses):
        self.current = StubCursor(responses)
        self.cursor_calls = 0

    def cursor(self):
        self.cursor_calls += 1
        return self.current


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 10, 1)
        self.end = datetime(2026, 11, 1)

    def test_catalog_combines_names_and_observation_statistics(self):
        observations = [
            (12345, 3, self.start, self.end, 8),
            (12346, 4, self.start, self.end, 5),
            (99999, 1, self.start, self.end, 2),
        ]
        conn = StubConnection([
            [(12345, 3, "ZN example"), (12346, 4, None)],
            observations,
        ])
        result = list_cyclones(conn, self.start, self.end)
        self.assertEqual([(r.cic_id, r.type_name) for r in result],
                         [(99999, "TC"), (12345, "ZN"), (12346, "AZ")])
        self.assertEqual(result[1].name, "ZN example")
        self.assertEqual(result[1].observation_count, 8)
        self.assertEqual(result[0].name, None)
        self.assertEqual(len(conn.current.calls), 2)
        self.assertTrue(conn.current.closed)
        self.assertEqual(conn.current.calls[0][1], (self.start, self.end, [1, 3, 4]))

    def test_empty_type_filter_skips_database(self):
        conn = StubConnection([])
        self.assertEqual(list_cyclones(conn, self.start, self.end, []), [])
        self.assertEqual(conn.cursor_calls, 0)

    def test_invalid_type_filter_is_rejected(self):
        with self.assertRaises(ValueError):
            list_cyclones(StubConnection([]), self.start, self.end, [999])


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 10, 1)
        self.end = datetime(2026, 11, 1)

    def test_ids_are_applied_to_both_queries(self):
        conn = StubConnection([[("point",)], [("track",)]])
        points, tracks = load_source_rows(conn, self.start, self.end, [12345, 12346, 12345])
        self.assertEqual((points, tracks), ([("point",)], [("track",)]))
        self.assertEqual(len(conn.current.calls), 2)
        for query, params in conn.current.calls:
            self.assertIn("AND cic_id = ANY(%s)", query)
            self.assertEqual(params, (self.start, self.end, [12345, 12346]))

    def test_none_keeps_existing_unfiltered_queries(self):
        conn = StubConnection([[], []])
        load_source_rows(conn, self.start, self.end)
        for query, params in conn.current.calls:
            self.assertNotIn("AND cic_id = ANY", query)
            self.assertEqual(params, (self.start, self.end))

    def test_empty_ids_do_not_execute_queries(self):
        conn = StubConnection([])
        self.assertEqual(load_source_rows(conn, self.start, self.end, []), ([], []))
        self.assertEqual(conn.cursor_calls, 0)

    def test_generator_passes_id_filter_without_changing_cli_signature(self):
        config = SimpleNamespace(
            db_host="localhost", db_port="5432", db_name="test",
            db_user="test", db_password="test",
            smb_host="", smb_username="", smb_password="", smb_share="",
        )
        from engine.models import PreparedRows
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(functions, "load_config", return_value=config),
            patch.object(functions.psycopg2, "connect", return_value=MagicMock()),
            patch.object(functions, "load_source_rows", return_value=([], [])) as loader,
            patch.object(functions, "prepare_rows", return_value=PreparedRows()),
            patch.object(functions, "render_map", return_value=MagicMock()),
        ):
            prefix = str(Path(directory) / "cyclone_")
            functions.main(False, False, False, "2026-10-01", 0, prefix,
                           False, False, "None", False, False,
                           is_save_csv=False, selected_cic_ids=[12345])
            self.assertEqual(loader.call_args.kwargs["selected_cic_ids"], [12345])
            loader.reset_mock()
            functions.main(False, False, False, "2026-10-01", 0, prefix,
                           False, False, "None", False, False, is_save_csv=False)
            self.assertNotIn("selected_cic_ids", loader.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
