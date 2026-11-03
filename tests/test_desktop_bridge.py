"""JSON desktop bridge integration tests (no real database or SMB)."""

import io
import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import desktop_bridge as bridge
from engine.catalog import CycloneInfo
from engine.models import PreparedRows


class BridgeTests(unittest.TestCase):
    def test_list_cyclones_returns_serializable_metadata(self):
        connection = MagicMock()
        entry = CycloneInfo(
            cic_id=12345,
            cic_type_id=1,
            name="TEST",
            first_observation=datetime(2026, 10, 1),
            last_observation=datetime(2026, 10, 2),
            observation_count=9,
        )
        with (
            patch.object(bridge, "_connect", return_value=connection),
            patch.object(bridge, "list_cyclones", return_value=[entry]) as query,
        ):
            response = bridge.dispatch({
                "action": "list-cyclones",
                "start_date": "2026-10-01",
                "period": 0,
                "types": [1],
            })
        self.assertEqual(response["cyclones"][0]["cic_id"], 12345)
        self.assertEqual(response["cyclones"][0]["type_name"], "TC")
        self.assertEqual(response["cyclones"][0]["first_observation"], "2026-10-01T00:00:00")
        self.assertEqual(query.call_args.args[3], [1])
        connection.close.assert_called_once()
        json.dumps(response)

    def test_preview_is_in_memory_and_does_not_call_legacy_generator(self):
        import functions
        import engine.renderer

        connection = MagicMock()
        image = bytes([137, 80, 78, 71, 13, 10, 26, 10])
        with (
            patch.object(bridge, "_connect", return_value=connection),
            patch.object(bridge, "load_source_rows", return_value=([], [])) as query,
            patch.object(bridge, "prepare_rows", return_value=PreparedRows()),
            patch.object(engine.renderer, "render_png_bytes", return_value=image) as renderer,
            patch.object(functions, "main") as legacy_main,
            patch.object(functions, "upload_file_to_smb") as smb,
        ):
            result = bridge.dispatch({
                "action": "preview",
                "start_date": "2026-10-01",
                "types": [1],
                "selected_cic_ids": [12345],
                "dpi": 40,
            })
        self.assertEqual(result["encoding"], "base64")
        self.assertEqual(result["image_base64"], "iVBORw0KGgo=")
        self.assertEqual(query.call_args.kwargs["selected_cic_ids"], [12345])
        self.assertEqual(renderer.call_args.kwargs["dpi"], 40)
        legacy_main.assert_not_called()
        smb.assert_not_called()
        connection.close.assert_called_once()

    def test_generate_disables_smb_by_default_and_passes_ids(self):
        import functions

        with patch.object(functions, "main") as legacy_main:
            result = bridge.dispatch({
                "action": "generate",
                "start_date": "2026-10-01",
                "types": [1],
                "save_path": "./test-data/",
                "selected_cic_ids": [42],
            })
        self.assertEqual(result["status"], "completed")
        kwargs = legacy_main.call_args.kwargs
        self.assertFalse(kwargs["is_smb"])
        self.assertTrue(kwargs["is_save_fig"])
        self.assertTrue(kwargs["is_save_csv"])
        self.assertEqual(kwargs["selected_cic_ids"], [42])

    def test_generate_rejects_smb_without_png(self):
        with self.assertRaisesRegex(ValueError, "requires save_png"):
            bridge.dispatch({
                "action": "generate",
                "start_date": "2026-10-01",
                "types": [1],
                "save_path": "./output/",
                "upload_smb": True,
                "save_png": False,
            })

    def test_json_protocol_keeps_prints_out_of_stdout(self):
        incoming = io.StringIO('{"action":"preview"}\n')
        outgoing = io.StringIO()
        diagnostics = io.StringIO()

        def fake_dispatch(request):
            print("internal diagnostic")
            return {"message": "done"}

        with (
            patch.object(bridge.sys, "stdin", incoming),
            patch.object(bridge.sys, "stdout", outgoing),
            patch.object(bridge.sys, "stderr", diagnostics),
            patch.object(bridge, "dispatch", side_effect=fake_dispatch),
        ):
            code = bridge.main()

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(outgoing.getvalue()), {"ok": True, "data": {"message": "done"}})
        self.assertIn("internal diagnostic", diagnostics.getvalue())
        self.assertNotIn("internal diagnostic", outgoing.getvalue())

    def test_invalid_request_returns_structured_error(self):
        incoming = io.StringIO("{bad json}\n")
        outgoing = io.StringIO()
        diagnostics = io.StringIO()
        with (
            patch.object(bridge.sys, "stdin", incoming),
            patch.object(bridge.sys, "stdout", outgoing),
            patch.object(bridge.sys, "stderr", diagnostics),
        ):
            code = bridge.main()
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(outgoing.getvalue())["ok"])

    def test_selected_ids_must_be_positive_integers(self):
        with self.assertRaises(ValueError):
            bridge.dispatch({
                "action": "preview",
                "start_date": "2026-10-01",
                "types": [1],
                "selected_cic_ids": [True],
            })

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(ValueError):
            bridge.dispatch({
                "action": "preview",
                "start_date": "2026-02-30",
                "types": [1],
            })


if __name__ == "__main__":
    unittest.main()
