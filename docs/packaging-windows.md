# Packaging CycloneTrackGenerator as a Windows EXE

The distributable is **CycloneEngine.exe**, an independent Python backend for the
WinForms UI. It uses the existing JSON-lines protocol from desktop_bridge.py and
includes a Python interpreter, Matplotlib, Basemap, psycopg2, SMB client, and
other Python dependencies.

It does **not** include WinForms/.NET, PostgreSQL, an SMB server, or user
credentials. Python is not needed on the target PC.

## 1. Build locally (Windows)

From the Python repository branch \`feature/pyinstaller-packaging\`, using the
working Conda environment:

\`\`\`powershell
conda activate PlotCysGener
python -m pip install "pyinstaller>=6,<7"
.\scripts\build_engine.ps1 -Python "C:\ProgramData\anaconda3\envs\PlotCysGener\python.exe"
\`\`\`

The script runs PyInstaller in **onedir** mode and then tests the actual
standalone executable by rendering a Basemap PNG **without connecting to a
database**. If packaging fails, stop and inspect the traceback.

Result:

\`\`\`text
dist/
  CycloneEngine/
    CycloneEngine.exe
    _internal/          # Python libraries, DLLs, Basemap/map data, etc.
\`\`\`

**Distribute the entire \`CycloneEngine\` folder, not only the EXE.**
This mode is intentional: the engine starts once per GUI operation, and onedir
avoids the repeated extraction overhead of PyInstaller onefile mode.

## 2. Build using GitHub Actions

The workflow \`.github/workflows/build-cyclone-engine.yml\` builds a Windows
x64 engine using Python 3.11. It runs Python tests, creates the EXE, performs
an offline Basemap rendering test, and publishes a downloadable
\`CycloneEngine-windows-x64\` artifact containing a ZIP distribution.

Open the repository's **Actions → Build CycloneEngine (Windows)** workflow
and download the artifact from the latest successful run. Extract the inner
\`CycloneEngine-windows-x64.zip\` if GitHub wraps the upload in an artifact ZIP.

## 3. Configure on the target PC

Keep \`confing.conf\` outside the package, in the same folder as the EXE:

\`\`\`text
CycloneEngine/
  CycloneEngine.exe
  confing.conf           # user-provided file; never commit or publish
  _internal/
\`\`\`

Keep the file readable only by the intended users; it contains database/SMB
credentials. The frozen program first respects a config file in its current
working directory and otherwise looks for one beside \`CycloneEngine.exe\`.

No Python/Conda installation is necessary, but PostgreSQL and optional SMB
still require working network access.

## 4. Test the packaged EXE

No credentials or database are required for the built-in health check:

\`\`\`powershell
'{"action":"self-test"}' | .\dist\CycloneEngine\CycloneEngine.exe
\`\`\`

Expected envelope (byte count varies):

\`\`\`json
{"ok":true,"data":{"status":"ok","rendered_png_bytes":12345}}
\`\`\`

Then test the real catalog from the folder containing \`confing.conf\`:

\`\`\`powershell
'{"action":"list-cyclones","start_date":"2026-10-01","period":0,"types":[1]}' | .\CycloneEngine.exe
\`\`\`

Also check \`preview\` and \`generate\` before rolling out to office users.
Those operations require the actual database, and \`generate\` can optionally
upload to SMB.

## 5. Integration with the WinForms UI

The current WinForms \`PythonBridgeClient\` starts \`python.exe -u
desktop_bridge.py\`. To use \`CycloneEngine.exe\` directly, update that client to
start the EXE **without** Python-specific flags or a .py script argument.

Do **not** simply enter the packaged EXE into the existing Python path field
before the GUI client supports this mode. A separate GUI integration change is
required.

## Notes

- Basemap uses native libraries and large coastline datasets. The spec
  explicitly includes Basemap, Matplotlib, and pyproj data. The smoke test
  checks that real PNG rendering works from the frozen bundle.
- The result is architecture- and OS-specific: build on Windows for Windows.
- If the user's Conda environment differs from CI's pip environment, build
  using the known-good local environment and verify on a clean Windows PC.
- Packaging does not protect passwords stored in \`confing.conf\` and does
  not remove network dependencies.
