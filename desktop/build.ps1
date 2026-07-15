param(
    [switch]$SkipInstall,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Dist = Join-Path $Root "dist"
$ProgramDir = Join-Path $Dist "XYZRender Workstation"

Push-Location $Root
try {
    if (-not $SkipInstall) {
        python -m pip install -r (Join-Path $PSScriptRoot "requirements-desktop.txt")
    }
    python -m PyInstaller --noconfirm --clean (Join-Path $PSScriptRoot "xyzrender_workstation.spec")
    $Exe = Join-Path $ProgramDir "XYZRender Workstation.exe"
    if (-not (Test-Path -LiteralPath $Exe)) {
        throw "PyInstaller did not create $Exe"
    }
    Write-Host "Program directory: $ProgramDir"

    if (-not $SkipInstaller) {
        $Candidates = @(
            (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
            (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe")
        )
        $Iscc = $Candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
        if (-not $Iscc) {
            $Command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
            if ($Command) { $Iscc = $Command.Source }
        }
        if (-not $Iscc) {
            throw "Inno Setup 6 was not found. Install it, then rerun with -SkipInstall."
        }
        & $Iscc (Join-Path $PSScriptRoot "installer.iss")
        Write-Host "Installer directory: $(Join-Path $Dist 'installer')"
    }
}
finally {
    Pop-Location
}
