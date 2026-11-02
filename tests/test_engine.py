import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from engine.config import load_config
from engine.database import get_cis_property_view_month, get_cis_track_view_month, load_source_rows
from engine.models import prepare_rows
from engine.periods import calculate_period


class StubCursor:
    def __init__(self):
        self.calls = []
        self.closed = False

    def execute(self, query, params):
        self.calls.append((query, params))

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True


class StubConnection:
    def __init__(self):
        self.cursor_obj = StubCursor()

    def cursor(self):
        return self.cursor_obj


class EngineTests(unittest.TestCase):
    def test_month_boundary_preserves_legacy_semantics(self):
        start, end = calculate_period("2026-01-31", 0)
        self.assertEqual((start, end), (datetime(2026, 1, 31), datetime(2026, 2, 28)))

    def test_decade_boundary_preserves_current_semantics(self):
        start, end = calculate_period("2026-10-21", -1)
        self.assertEqual((start, end), (datetime(2026, 10, 21), datetime(2026, 10, 31)))

    def test_custom_day_period(self):
        start, end = calculate_period("2026-10-05", 7)
        self.assertEqual(end - start, __import__("datetime").timedelta(days=7))

    def test_queries_use_bound_parameters(self):
        c = StubCursor()
        start, end = calculate_period("2026-10-01", 0)
        get_cis_property_view_month(start, end, c)
        get_cis_track_view_month(start, end, c)
        self.assertEqual(len(c.calls), 2)
        self.assertTrue(all(params == (start, end) for _, params in c.calls))
        self.assertTrue(all("%s" in sql for sql, _ in c.calls))

    def test_cursor_closes(self):
        connection = StubConnection()
        points, tracks = load_source_rows(connection, datetime(2026, 1, 1), datetime(2026, 2, 1))
        self.assertEqual((points, tracks), ([], []))
        self.assertTrue(connection.cursor_obj.closed)

    def test_prepare_rows_by_type_and_pressure(self):
        now = datetime(2026, 10, 1, 0, 0)
        track = ["LINESTRING(100 20,101 21)", 3, 1234, "sample"]
        dot = [None] * 19
        dot[0], dot[1], dot[2], dot[4], dot[13], dot[15], dot[18] = 100.0, 20.0, 3, 1234, 5, now, 998
        result = prepare_rows([track], [dot], True, False, False, True, True)
        self.assertEqual(len(result.track_view_zn), 1)
        self.assertEqual(len(result.mon_view_zn), 1)
        self.assertEqual(result.track_view_zn[0].id, "34")
        self.assertEqual(result.mon_view_zn[0].slp, 998)
        self.assertEqual(result.csv_dot_zn[0].slp, 998)
        self.assertEqual(len(result.track_view_az), 0)

    def test_config_parsing(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "confing.conf"
            path.write_text("dbhost\n5432\ncyclones\nuser\nsecret\nsmbhost\nsmbuser\nsmbpass\nshare\n", encoding="utf-8")
            config = load_config(str(path))
            self.assertEqual(config.db_host, "dbhost")
            self.assertEqual(config.smb_share, "share")


if __name__ == "__main__":
    unittest.main()
