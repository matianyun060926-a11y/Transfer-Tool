param(
    [string]$PythonCommand = "py"
)

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$iconScript = Join-Path $projectRoot "tools\generate_icon_assets.py"
$requirementsFile = Join-Path $projectRoot "windows-app\requirements-build.txt"
$iconPath = Join-Path $projectRoot "windows-app\resources\transfer-tool.ico"
$mainScript = Join-Path $projectRoot "windows-app\main.py"
$distFolder = Join-Path $projectRoot "dist"
$packagedExe = Join-Path $distFolder "TransferTool.exe"

Push-Location $projectRoot
try {
    & $PythonCommand -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & $PythonCommand $iconScript
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & $PythonCommand -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --onefile `
        --name TransferTool `
        --icon $iconPath `
        --add-data "web-app;web-app" `
        --add-data "windows-app\resources;windows-app\resources" `
        $mainScript
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Output ""
    Write-Output "Build complete."
    Write-Output "Single-file executable: $packagedExe"
    Write-Output "Share this file with others: $packagedExe"
}
finally {
    Pop-Location
}
