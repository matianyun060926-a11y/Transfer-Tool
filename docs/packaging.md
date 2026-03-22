# Packaging

## Goal

Create a standalone Windows executable using PyInstaller so the app can launch like a normal desktop utility.

## Build Script

Run:

```powershell
powershell -ExecutionPolicy Bypass -File windows-app\scripts\build_pyinstaller.ps1
```

The script:

1. installs build dependencies from `windows-app\requirements-build.txt`
2. regenerates the icon assets
3. runs PyInstaller in windowed mode
4. bundles:
   - the desktop app code
   - the mobile web app files
   - the Windows icon/resources
   - the helper scripts

## Output Folder

The packaged app is written to:

`dist\TransferTool\`

The main executable in that folder is:

`dist\TransferTool\TransferTool.exe`

The build script also creates:

`dist\TransferTool\Open Transfer Tool.bat`

That batch file is a portable convenience launcher that works relative to the packaged folder, so the folder can still be moved to another PC.

The `build\` and `dist\` folders are ignored by Git.

## Icon Attachment

The executable icon comes from:

`windows-app\resources\transfer-tool.ico`

The build script attaches it with PyInstaller's `--icon` option.

The same icon family is also used for:

- the desktop window
- the favicon
- the Safari touch icon

## Shortcut Target After Packaging

After packaging, the main thing to click in the distributed folder is:

`dist\TransferTool\TransferTool.exe`

There is also a clearer text launcher next to it:

`dist\TransferTool\Open Transfer Tool.bat`

If you still want a Windows desktop shortcut, the preferred shortcut target is:

`dist\TransferTool\TransferTool.exe`

That is what:

- the fallback PowerShell shortcut script targets when that executable exists

## Source Mode vs Packaged Mode

### Source mode

Pros:

- easiest while developing
- no build step needed

Cons:

- still depends on local Python
- uses the launcher batch file

### Packaged mode

Pros:

- launches like a normal Windows app
- better for day-to-day personal use

Cons:

- requires a PyInstaller build step
