# Packaging

## Goal

Build a single Windows executable that can be shared directly with other people.

## Build Script

Run:

```powershell
powershell -ExecutionPolicy Bypass -File windows-app\scripts\build_pyinstaller.ps1
```

The script:

1. installs build dependencies from `windows-app\requirements-build.txt`
2. regenerates the icon assets
3. runs PyInstaller in one-file windowed mode
4. bundles:
   - the desktop app code
   - the mobile web app files
   - the Windows icon/resources

## Output

The packaged app is written to:

`dist\TransferTool.exe`

This is the file you can send to someone else directly.

## Runtime Data

When the packaged app runs, it stores settings, logs, history, and received files under the current user's local app data folder:

`%LOCALAPPDATA%\TransferTool\`

That avoids write-permission problems when the `exe` is launched from read-only or temporary locations.

## Icon Attachment

The executable icon comes from:

`windows-app\resources\transfer-tool.ico`

The build script attaches it with PyInstaller's `--icon` option.
