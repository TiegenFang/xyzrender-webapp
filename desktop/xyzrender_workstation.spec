# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata


ROOT = Path(SPEC).resolve().parents[1]
SRC = ROOT / "src"

datas = [
    (str(ROOT / "MOLECULES"), "MOLECULES"),
    (str(SRC / "xyzrender_workstation" / "web" / "templates"), "xyzrender_workstation/web/templates"),
    (str(SRC / "xyzrender_workstation" / "web" / "static"), "xyzrender_workstation/web/static"),
]
binaries = []
hiddenimports = (
    collect_submodules("xyzrender")
    + collect_submodules("xyzgraph")
    + collect_submodules("ase.io")
    + ["scipy._cyutility"]
)
datas += collect_data_files("xyzrender")
datas += collect_data_files("xyzgraph")
datas += collect_data_files("rdkit")
datas += collect_data_files("ase")
for distribution in ("xyzrender", "xyzgraph", "Flask", "pywebview", "numpy", "ase", "rdkit"):
    try:
        datas += copy_metadata(distribution)
    except Exception:
        pass

a = Analysis(
    [str(ROOT / "desktop" / "launcher.py")],
    pathex=[str(ROOT), str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "PyQt5", "PyQt6", "PySide2", "PySide6", "tkinter",
        "torch", "torchvision", "vtk", "sklearn", "skimage", "pandas",
        "pyarrow", "IPython", "notebook", "sqlalchemy", "pygame", "wx",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="XYZRender Workstation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(ROOT / "desktop" / "assets" / "xyzrender-workstation.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="XYZRender Workstation",
)
