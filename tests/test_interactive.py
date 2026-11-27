import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import desktop_bridge as bridge
from engine.models import PreparedRows, TrackRow, DotRow
from engine.hitmap import render_interactive, clip_segment


class InteractiveTests(unittest.TestCase):
    def test_actual_render(self):
        from PIL import Image
        from io import BytesIO
        p = PreparedRows(
            track_view_zn=[TrackRow("LINESTRING(140 40,145 45)", "test", "01", 101)],
            mon_view_zn=[DotRow(140, 40, None, "", datetime(2026, 1, 1), 10101, 101),
                         DotRow(145, 45, None, "", datetime(2026, 1, 2), 10102, 101)])
        png, meta = render_interactive(p, True, False, "None", dpi=60)
        with Image.open(BytesIO(png)) as img:
            self.assertEqual(img.size, (meta["width"], meta["height"]))
            self.assertEqual([p["observation_id"] for p in meta["points"]], [10101, 10102])
            self.assertEqual(meta["tracks"][0]["cic_id"], 101)
            for p, endpoint in zip(meta["points"], meta["tracks"][0]["segments"][0]):
                self.assertAlmostEqual(p["x"], endpoint[0], places=3)
                self.assertAlmostEqual(p["y"], endpoint[1], places=3)
                x, y = round(p["x"]), round(p["y"])
                pixels = list(img.convert("RGB").crop((x-5, y-5, x+6, y+6)).getdata())
                self.assertTrue(any(b > r + 30 and b > g + 30 for r, g, b in pixels))

    def test_clip(self):
        self.assertEqual(clip_segment((-5, 5), (15, 5), (0, 0, 10, 10)), ((0, 5), (10, 5)))
        self.assertIsNone(clip_segment((-5, -5), (-1, -1), (0, 0, 10, 10)))

    def test_readonly_card(self):
        conn = MagicMock()
        with patch.object(bridge, "_connect", return_value=conn), \
             patch("engine.editing.get_record", return_value={"id": 42}) as get:
            self.assertEqual(bridge.dispatch({"action":"get-observation", "id":42}),
                             {"record":{"id":42}})
        conn.set_session.assert_called_once_with(readonly=True)
        get.assert_called_once_with(conn, "observation", 42)
        conn.close.assert_called_once()

    def test_invalid_and_update_rejected(self):
        for request in [{"action":"get-observation", "id":True},
                        {"action":"get-cyclone", "id":0}, {"action":"update-observation", "id":42}]:
            with self.assertRaises(ValueError):
                bridge.dispatch(request)
