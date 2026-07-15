# Windows desktop build

The desktop application keeps the existing Flask routes and HTML UI. `pywebview`
hosts the local-only Flask service in a native window; no HTTP resource is loaded
from the public internet.

## Build

Install Python 3.10+ x64 and Inno Setup 6, then run from PowerShell:

```powershell
.\desktop\build.ps1
```

The script produces:

- `dist\XYZRender Workstation\` — PyInstaller **onedir** program directory.
- `dist\installer\XYZRender-Workstation-1.0.0-Setup.exe` — Inno Setup installer.

Use `-SkipInstall` after dependencies are installed, or `-SkipInstaller` when only
the onedir output is needed.

Verify the frozen program without opening a window:

```powershell
& ".\dist\XYZRender Workstation\XYZRender Workstation.exe" --self-test --data-dir ".\dist-self-test-data"
$LASTEXITCODE
Get-Content ".\dist-self-test-data\logs\self-test.json"
```

## Runtime data and diagnostics

Installed binaries and bundled examples are read-only resources. Writable data is
stored outside the installation directory:

```text
%LOCALAPPDATA%\XYZRender Workstation\
├── MOLECULES\
├── TEMP\
├── FIGURE\
└── logs\xyzrender-workstation.log
```

The launcher copies missing bundled examples on first run without overwriting user
files. The installer does not own this directory, so upgrades and uninstall leave
user molecules, figures, previews and logs intact.

The log records resource/data paths, packaged dependency versions, Flask startup,
uncaught request failures and rendering failures. A startup failure also displays
the log location in a native error dialog.
