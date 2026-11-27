"""Pixel metadata from the actual plotted artists; no database access."""
import math
import struct
from io import BytesIO


def clip_segment(a, b, bounds):
    """Liang-Barsky clipping to the visible map axes (display pixels)."""
    x0, y0, x1, y1 = bounds
    x, y = a
    dx, dy = b[0] - x, b[1] - y
    lo, hi = 0.0, 1.0
    for p, q in ((-dx, x-x0), (dx, x1-x), (-dy, y-y0), (dy, y1-y)):
        if p == 0:
            if q < 0:
                return None
        else:
            t = q / p
            if p < 0:
                lo = max(lo, t)
            else:
                hi = min(hi, t)
            if lo > hi:
                return None
    return ((x+lo*dx, y+lo*dy), (x+hi*dx, y+hi*dy))


def render_interactive(prepared, cys_type_zn, cys_type_az, blanc_type, dpi=75):
    from matplotlib import pyplot as plt
    from .renderer import render_map

    artists = []
    figure = render_map(prepared, cys_type_zn, cys_type_az, blanc_type, hits=artists)
    try:
        # Use the SAME explicit crop and DPI for metadata and PNG. Do not
        # recalculate a tight bounding box after collecting coordinates.
        figure.set_dpi(dpi)
        figure.canvas.draw()
        crop = figure.get_tightbbox(figure.canvas.get_renderer()).padded(0.1)
        crop_px = crop.transformed(figure.dpi_scale_trans)
        records = []
        for kind, key, cic_id, artist in artists:
            if key is None or cic_id is None:
                continue
            vertices = artist.get_transform().transform(artist.get_xydata())
            bounds = artist.axes.bbox.extents
            records.append((kind, int(key), int(cic_id), vertices.tolist(), tuple(bounds)))

        with BytesIO() as buf:
            figure.savefig(buf, format="png", dpi=dpi, bbox_inches=crop)
            png = buf.getvalue()
        width, height = struct.unpack(">II", png[16:24])

        def pixel(p):
            return [round(p[0] - crop_px.x0, 3),
                    round(height - (p[1] - crop_px.y0), 3)]

        points, tracks = [], {}
        for kind, key, cic_id, vertices, bounds in records:
            if kind == "point":
                if len(vertices) != 1:
                    continue
                x, y = vertices[0]
                if (math.isfinite(x) and math.isfinite(y)
                        and bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]):
                    px, py = pixel((x, y))
                    if 0 <= px < width and 0 <= py < height:
                        points.append({"observation_id": key, "cic_id": cic_id, "x": px, "y": py})
                continue
            for a, b in zip(vertices, vertices[1:]):
                if not all(math.isfinite(v) for v in (*a, *b)):
                    continue
                clipped = clip_segment(a, b, bounds)
                if clipped is not None:
                    tracks.setdefault(key, []).append([pixel(clipped[0]), pixel(clipped[1])])
        return png, {"width": width, "height": height, "points": points,
                     "tracks": [{"cic_id": key, "segments": segments}
                                for key, segments in tracks.items()]}
    finally:
        plt.close(figure)
