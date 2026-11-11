"""One-request-per-process JSON bridge for a .NET desktop application.

Protocol: one UTF-8 JSON object per stdin line; one JSON response on stdout.
Diagnostics, including legacy print() calls, go to stderr. Launch with the
repository root as the working directory to resolve confing.conf.
"""

import base64
from contextlib import redirect_stdout
from datetime import datetime
import json
import os
import sys
import traceback

os.environ.setdefault("MPLBACKEND", "Agg")

from engine.catalog import list_cyclones
from engine.config import load_config
from engine.database import load_source_rows
from engine.models import prepare_rows
from engine.periods import calculate_period


ALLOWED_TYPES = {1, 3, 4}


def _boolean(request, key, default=False):
    value = request.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a JSON boolean")
    return value


def _integer(request, key, default):
    value = request.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _string(request, key, default=None):
    value = request.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _types(request):
    types = request.get("types", [1, 3, 4])
    if not isinstance(types, list):
        raise ValueError("types must be an array of cyclone type IDs")
    if any(isinstance(i, bool) or not isinstance(i, int) or i not in ALLOWED_TYPES for i in types):
        raise ValueError("types may only contain the integer IDs 1 (TC), 3 (ZN), and 4 (AZ)")
    return list(dict.fromkeys(types))


def _selected_ids(request):
    ids = request.get("selected_cic_ids")
    if ids is None:
        return None
    if not isinstance(ids, list):
        raise ValueError("selected_cic_ids must be null or an array of integer IDs")
    if any(isinstance(i, bool) or not isinstance(i, int) or i <= 0 for i in ids):
        raise ValueError("selected_cic_ids must contain positive integer IDs")
    return list(dict.fromkeys(ids))


def _date_range(request):
    start_date = _string(request, "start_date")
    period = _integer(request, "period", 0)
    if period < -1:
        raise ValueError("period must be -1 (decade), 0 (month), or a positive day count")
    start, end = calculate_period(start_date, period)
    return start, end, period


def _options(request):
    types = _types(request)
    if not types:
        raise ValueError("Select at least one cyclone type")
    blank = request.get("blanc_type", "TC" if types == [1] else "None")
    if blank not in ("None", "TC"):
        raise ValueError("blanc_type must be 'None' or 'TC'")
    return types, blank, _selected_ids(request)


def _connect(config_path):
    import psycopg2

    config = load_config(config_path)
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def _catalog(request):
    start, end, _ = _date_range(request)
    types = _types(request)
    if not types:
        return {"cyclones": []}

    conn = _connect(_string(request, "config_path", "confing.conf"))
    try:
        cyclones = list_cyclones(conn, start, end, types)
    finally:
        conn.close()

    return {
        "cyclones": [
            {
                "cic_id": c.cic_id,
                "type_id": c.cic_type_id,
                "type_name": c.type_name,
                "name": c.name,
                "first_observation": c.first_observation.isoformat() if c.first_observation else None,
                "last_observation": c.last_observation.isoformat() if c.last_observation else None,
                "observation_count": c.observation_count,
            }
            for c in cyclones
        ]
    }


def _preview(request):
    start, end, _ = _date_range(request)
    types, blank, ids = _options(request)
    show_pressure = _boolean(request, "show_pressure")
    show_names = _boolean(request, "show_names", True)
    dpi = _integer(request, "dpi", 75)
    if dpi < 20 or dpi > 300:
        raise ValueError("dpi must be between 20 and 300")

    conn = _connect(_string(request, "config_path", "confing.conf"))
    try:
        points, tracks = load_source_rows(conn, start, end, selected_cic_ids=ids)
    finally:
        conn.close()

    prepared = prepare_rows(
        tracks, points,
        3 in types, 4 in types, 1 in types,
        show_pressure, show_names,
    )
    from engine.renderer import render_png_bytes

    png = render_png_bytes(prepared, 3 in types, 4 in types, blank, dpi=dpi)
    return {
        "mime_type": "image/png",
        "encoding": "base64",
        "image_base64": base64.b64encode(png).decode("ascii"),
        "byte_length": len(png),
    }


def _generate(request):
    start, _, period = _date_range(request)
    types, blank, ids = _options(request)
    save_path = _string(request, "save_path")
    show_pressure = _boolean(request, "show_pressure")
    show_names = _boolean(request, "show_names", True)
    save_png = _boolean(request, "save_png", True)
    save_csv = _boolean(request, "save_csv", True)
    upload_smb = _boolean(request, "upload_smb", False)

    if not save_png and not save_csv:
        raise ValueError("Enable save_png or save_csv to produce an output")
    if upload_smb and not save_png:
        raise ValueError("Current legacy SMB export requires save_png=true")
    if request.get("config_path", "confing.conf") != "confing.conf":
        raise ValueError("generate currently uses the legacy confing.conf in the working directory")

    # This is the same generator used by main.py, with SMB explicitly opt-in.
    from functions import main as generate_main

    generate_main(
        3 in types, 4 in types, 1 in types,
        start.strftime("%Y-%m-%d"), period, save_path,
        show_pressure, show_names, blank,
        is_smb=upload_smb, is_save_fig=save_png, is_save_csv=save_csv,
        selected_cic_ids=ids,
    )

    return {
        "status": "completed",
        "save_path": save_path,
        "smb_requested": upload_smb,
    }


def _self_test(request):
    """Exercise native imports and Basemap rendering without credentials or DB."""
    import psycopg2  # noqa: F401 - detect missing bundled native dependencies
    import smbclient  # noqa: F401 - verify SMB client is included

    from engine.renderer import render_png_bytes
    from engine.models import PreparedRows

    png = render_png_bytes(
        PreparedRows(),
        cys_type_zn=False,
        cys_type_az=False,
        blanc_type="None",
        dpi=35,
    )
    if not png.startswith(bytes([137, 80, 78, 71, 13, 10, 26, 10])):
        raise RuntimeError("Renderer did not return valid PNG bytes")

    return {"status": "ok", "rendered_png_bytes": len(png)}


def dispatch(request):
    """Return the action result. No protocol output is printed here."""
    if not isinstance(request, dict):
        raise ValueError("Request must be a JSON object")
    action = request.get("action")
    if action == "self-test":
        return _self_test(request)
    if action == "list-cyclones":
        return _catalog(request)
    if action == "preview":
        return _preview(request)
    if action == "generate":
        return _generate(request)
    raise ValueError("Unknown action; expected self-test, list-cyclones, preview, or generate")


def main():
    # Accept a single line so the GUI need not close the process stdin first.
    line = sys.stdin.readline()
    try:
        if not line.strip():
            raise ValueError("Expected one JSON request on stdin")
        request = json.loads(line)
        # Existing helper functions may print progress; keep stdout pure JSON.
        with redirect_stdout(sys.stderr):
            response = dispatch(request)
        payload = {"ok": True, "data": response}
        code = 0
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        payload = {"ok": False, "error": {"type": type(exc).__name__, "message": str(exc)}}
        code = 1

    sys.stdout.write(json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()
    return code


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(main())
