# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onedir bundle for the Windows desktop JSON engine.

Run from the Python repository root:
    python -m PyInstaller --noconfirm --clean CycloneEngine.spec

No credentials, local config, screenshots or user data are bundled.
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


ROOT = Path.cwd()
if not (ROOT / "desktop_bridge.py").is_file():
    raise RuntimeError("Run PyInstaller from the CycloneTrackGenerator repository root")

# Basemap coastline data live in a separate basemap-data distribution.
# matplotlib and pyproj also use non-Python assets (fonts, PROJ database).
data_files = []
for package in (
    "mpl_toolkits.basemap_data",
    "mpl_toolkits.basemap",
    "matplotlib",
    "pyproj",
):
    data_files += collect_data_files(package)

a = Analysis(
    ["desktop_bridge.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=data_files,
    hiddenimports=[
        "functions",
        "smbclient",
        "psycopg2",
        "engine.renderer",
        "mpl_toolkits.basemap",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CycloneEngine",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # Required for JSON stdin/stdout protocol.
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="CycloneEngine",
)
