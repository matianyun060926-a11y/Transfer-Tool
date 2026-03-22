param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$PackagedExecutable = "",
    [string]$ShortcutName = "Transfer Tool"
)

$projectRootPath = (Resolve-Path $ProjectRoot).Path
$packagedCandidate = Join-Path $projectRootPath "dist\TransferTool\TransferTool.exe"
$launchBatch = Join-Path $projectRootPath "windows-app\launch_transfer_tool.bat"
$iconPath = Join-Path $projectRootPath "windows-app\resources\transfer-tool.ico"

if ($PackagedExecutable -and (Test-Path $PackagedExecutable)) {
    $targetPath = (Resolve-Path $PackagedExecutable).Path
    $workingDirectory = Split-Path $targetPath
}
elseif (Test-Path $packagedCandidate) {
    $targetPath = (Resolve-Path $packagedCandidate).Path
    $workingDirectory = Split-Path $targetPath
}
else {
    $targetPath = (Resolve-Path $launchBatch).Path
    $workingDirectory = $projectRootPath
}

if (-not (Test-Path $iconPath)) {
    $iconPath = $targetPath
}

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "$ShortcutName.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $workingDirectory
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = "Transfer Tool local LAN transfer utility"
$shortcut.Save()

Write-Output "Created desktop shortcut: $shortcutPath"
Write-Output "Shortcut target: $targetPath"

