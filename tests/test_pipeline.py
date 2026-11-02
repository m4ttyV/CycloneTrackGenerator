"""Integration tests for the CLI pipeline, without real PostgreSQL or SMB."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import functions
from engine.models import CSVRow, PreparedRows


class PipelineTests(unittest.TestCase):
    def run_case(self, save_csv):
        prepared = PreparedRows(
            csv_dot_zn=[CSVRow("01", __import__("datetime").datetime(2026, 10, 1), 140, 45, 980)],
            csv_dot_az=[CSVRow("02", __import__("datetime").datetime(2026, 10, 1), 141, 46, 1020)],
            csv_dot_tc=[CSVRow("03", __import__("datetime").datetime(2026, 10, 1), 142, 47, 970)],
        )
        config = SimpleNamespace(
            db_host="localhost", db_port="5432", db_name="test", db_user="test", db_password="test",
            smb_host="", smb_username="", smb_password="", smb_share="",
        )
        connection = MagicMock()
        figure = MagicMock()
        with tempfile.TemporaryDirectory() as directory:
            # The legacy save_path is a file prefix, not an output directory.
            prefix = str(Path(directory) / "cyclone_")
            with (
                patch.object(functions, "load_config", return_value=config),
                patch.object(functions.psycopg2, "connect", return_value=connection),
                patch.object(functions, "load_source_rows", return_value=([], [])),
                patch.object(functions, "prepare_rows", return_value=prepared),
                patch.object(functions, "render_map", return_value=figure),
                patch.object(functions, "upload_file_to_smb") as upload,
                patch.object(functions, "csv_gen", wraps=functions.csv_gen) as csv_export,
            ):
                functions.main(
                    True, True, True, "2026-10-01", 0, prefix,
                    False, True, "None", is_smb=False, is_save_fig=False,
                    is_save_csv=save_csv,
                )
                self.assertEqual(csv_export.call_count, 3 if save_csv else 0)
                for kind in ("ZN", "AZ", "TC"):
                    filename = Path(directory) / f"cyclone_20261001_month_{kind}.csv"
                    self.assertEqual(filename.exists(), save_csv)
                upload.assert_not_called()
                figure.savefig.assert_not_called()
                connection.close.assert_called_once()

    def test_csv_export_uses_prepared_rows_for_all_types(self):
        self.run_case(save_csv=True)

    def test_csv_export_can_be_disabled(self):
        self.run_case(save_csv=False)


if __name__ == "__main__":
    unittest.main()
