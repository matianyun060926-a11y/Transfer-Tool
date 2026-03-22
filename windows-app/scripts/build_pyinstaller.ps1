param(
    [string]$PythonCommand = "py"
)

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$iconScript = Join-Path $projectRoot "tools\generate_icon_assets.py"
$requirementsFile = Join-Path $projectRoot "windows-app\requirements-build.txt"
$iconPath = Join-Path $projectRoot "windows-app\resources\transfer-tool.ico"
$mainScript = Join-Path $projectRoot "windows-app\main.py"
$distFolder = Join-Path $projectRoot "dist\TransferTool"
$packagedExe = Join-Path $distFolder "TransferTool.exe"
$portableLauncher = Join-Path $distFolder "Open Transfer Tool.bat"

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
        --name TransferTool `
        --icon $iconPath `
        --add-data "web-app;web-app" `
        --add-data "windows-app\resources;windows-app\resources" `
        --add-data "windows-app\scripts;scripts" `
        $mainScript
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    @"
@echo off
setlocal
cd /d "%~dp0"
"%~dp0TransferTool.exe"
"@ | Set-Content -Path $portableLauncher -Encoding ASCII

    Write-Output ""
    Write-Output "Build complete."
    Write-Output "Packaged folder: $distFolder"
    Write-Output "Main executable: $packagedExe"
    Write-Output "Portable launcher: $portableLauncher"
    Write-Output "After packaging, open the folder and click TransferTool.exe or Open Transfer Tool.bat"
}
finally {
    Pop-Location
}
