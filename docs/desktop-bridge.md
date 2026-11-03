# Desktop JSON bridge

`desktop_bridge.py` exposes cyclone data to a .NET desktop application.
It is independent of Avalonia, WPF, or WinForms. The original `main.py`
remains unchanged.

## Process protocol

Launch `python desktop_bridge.py` with the repository root as the process
working directory (the legacy config file is `confing.conf`).

- Send **one** UTF-8 JSON object followed by a newline on standard input.
- Read one complete JSON response line from standard output.
- Read standard error concurrently for diagnostics; legacy print calls are
  redirected there.
- Exit code 0 indicates a successful action, 1 an error. An error still
  produces JSON on stdout.
- The bridge handles one request, then exits. For cancellation, terminate the
  child process and dispose of it in the host application.
- Do not block on process exit before reading stdout/stderr: PNG previews can
  result in large JSON responses and pipe buffers can fill up.

Successful envelope:

```json
{"ok":true,"data":{"cyclones":[]}}
```

Error envelope (example):

```json
{"ok":false,"error":{"type":"ValueError","message":"Select at least one cyclone type"}}
```

All dates are strings of the form `YYYY-MM-DD`. `period`: `0` for a
month, `-1` for a decade, and a positive integer for a number of days.
The period selection retains existing legacy boundary rules.

Types are integer IDs: `1` = tropical cyclones (TC), `3` = cyclones (ZN),
`4` = anticyclones (AZ). `selected_cic_ids: null` or an omitted field
selects all matching IDs; `[]` selects none.

## List cyclones

Request:

```json
{"action":"list-cyclones","start_date":"2026-10-01","period":0,"types":[1]}
```

Response data:

```json
{
  "cyclones": [
    {
      "cic_id": 12345,
      "type_id": 1,
      "type_name": "TC",
      "name": "EXAMPLE",
      "first_observation": "2026-10-01T00:00:00",
      "last_observation": "2026-10-03T00:00:00",
      "observation_count": 9
    }
  ]
}
```

Values above are illustrative, not actual database results.

## Preview PNG in memory

Request:

```json
{"action":"preview","start_date":"2026-10-01","period":0,"types":[1],"selected_cic_ids":[12345],"show_pressure":false,"show_names":true,"blanc_type":"TC","dpi":75}
```

Response data contains:

- `mime_type: "image/png"`
- `encoding: "base64"`
- `image_base64`: complete PNG bytes encoded as Base64
- `byte_length`: the unencoded PNG size

Decode `image_base64` in .NET and display the bytes. Preview creates no
PNG/CSV files and never uploads to SMB.

## Generate/export

Request:

```json
{"action":"generate","start_date":"2026-10-01","period":0,"types":[1],"selected_cic_ids":[12345],"save_path":"./test-data/","show_pressure":false,"show_names":true,"blanc_type":"TC","save_png":true,"save_csv":true,"upload_smb":false}
```

Response data:

```json
{"status":"completed","save_path":"./test-data/","smb_requested":false}
```

The legacy generator interprets `save_path` as a **file-name prefix**.
Use a trailing slash if you intend it as a directory; e.g. `./test-data/`.
The bridge requires `save_path` for export, and **never enables SMB unless
`upload_smb` is explicitly true**. The legacy uploader currently logs some
SMB failures without propagating exceptions; successful generation does not
guarantee a successful remote upload.

## Basic checks

From an activated project environment and the repository root:

```powershell
'{"action":"list-cyclones","start_date":"2026-10-01","period":0,"types":[1]}' | python desktop_bridge.py
python -m compileall -q main.py functions.py desktop_bridge.py engine tests
python -m unittest discover -s tests -v
```

The first command requires the real PostgreSQL configuration. The unit tests
use mocks and do not connect to PostgreSQL or upload to SMB.

For the desktop host, set `UseShellExecute=false`, redirect standard input,
output and error, configure UTF-8, and asynchronously consume both output pipes.
