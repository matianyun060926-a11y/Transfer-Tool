# Transfer Tool

Transfer Tool is a personal-use local network file transfer MVP for:

- Windows desktop
- iPhone / iPad in Safari

It is intentionally small and local:

- local Wi-Fi / LAN only
- no cloud
- no login
- no Xcode
- no Mac required
- no native mobile app pipeline

## What It Does

On Windows, the desktop app runs a local server and shows:

- the Windows PC local IP and URL
- a QR code for opening the local URL and completing one-time trusted pairing
- a 6-digit pairing code
- trusted Safari devices with revoke support
- received uploads
- shared files prepared for iPhone/iPad download
- transfer history
- diagnostics logs

On iPhone or iPad, Safari opens the Windows PC URL and provides a mobile-friendly web UI for:

- entering the pairing code
- restoring trusted access automatically for the same browser/device
- uploading one or more files to Windows
- downloading files that Windows shared
- viewing recent transfer history
- watching upload and download progress
- retrying or cancelling the current transfer

## Current Repo Structure

```text
Transfer Tool/
  web-app/
    index.html
    icon-192.png
    icon-512.png
    assets/
      app.js
      styles.css
  windows-app/
    launch_transfer_tool.bat
    main.py
    requirements.txt
    requirements-build.txt
    resources/
    scripts/
    transfer_tool/
      models/
      networking/
      services/
      ui/
    tests/
  branding/
  tools/
  docs/
    architecture.md
    protocol.md
    setup.md
    packaging.md
    troubleshooting.md
    manual-test-checklist.md
  runtime_data/
    received_files/
    transfer_history/
    logs/
  README.md
  .gitignore
```

## Runtime Data

Runtime-generated files live under `runtime_data/` and are ignored by Git.

Important folders:

- `runtime_data/received_files/`
- `runtime_data/transfer_history/`
- `runtime_data/logs/`
- `runtime_data/shared_files/`

## Quick Start

1. Install Python 3.13 or newer on Windows.
2. Create a virtual environment.
3. Install the dependencies from `windows-app/requirements.txt`.
4. Run `py windows-app/main.py`.
5. Open the displayed local URL in Safari on your iPhone/iPad, or scan the QR code from the desktop app to auto-pair.
6. If you did not use the QR code, enter the pairing code shown in the Windows app once to trust that Safari device.

## Docs

- [Architecture](C:/Users/Matt/Documents/GitHub/Transfer%20Tool/docs/architecture.md)
- [Protocol](C:/Users/Matt/Documents/GitHub/Transfer%20Tool/docs/protocol.md)
- [Setup](C:/Users/Matt/Documents/GitHub/Transfer%20Tool/docs/setup.md)
- [Packaging](C:/Users/Matt/Documents/GitHub/Transfer%20Tool/docs/packaging.md)
- [Troubleshooting](C:/Users/Matt/Documents/GitHub/Transfer%20Tool/docs/troubleshooting.md)
- [Manual Test Checklist](C:/Users/Matt/Documents/GitHub/Transfer%20Tool/docs/manual-test-checklist.md)

## Visual Refresh

The current UI pass uses one consistent design language across desktop and mobile:

- light background
- soft blue / teal accents
- gentle gray surfaces
- rounded cards and calmer spacing
- simpler status styling and cleaner hierarchy
- shared app icon for Windows and Safari

## Verification

Automated verification completed on the Python side with:

- `py -m compileall windows-app web-app`
- `py -m pytest windows-app/tests`

## Shortcut And Packaging

- Packaged executable build:
  - `powershell -ExecutionPolicy Bypass -File windows-app\scripts\build_pyinstaller.ps1`
  - packaged folder: `dist\TransferTool\`
  - main thing to click: `dist\TransferTool\TransferTool.exe`
  - optional launcher in the folder: `dist\TransferTool\Open Transfer Tool.bat`

- Secondary fallback PowerShell shortcut script:
  - `powershell -ExecutionPolicy Bypass -File windows-app\scripts\create_desktop_shortcut.ps1`

## What Works Now

- Windows-hosted local server
- Safari mobile UI
- QR code auto-pairing from the Windows app
- 6-digit pairing
- trusted-device restore for Safari
- iPhone/iPad upload to Windows
- Windows share for iPhone/iPad download
- a dedicated drop zone in the Windows app Shared Files tab
- retry and cancel controls for the current mobile transfer
- recent JSON history
- runtime data outside Git
- beginner-friendly docs and code structure

## Simplifications

- one hosted Windows server instead of peer-to-peer mobile hosting
- no automatic device discovery
- no background mobile transfers
- no resumable downloads/uploads
- shared Windows files stay available until manually removed

## Good Next Improvements

- expiring shared download links
- optional ZIP naming controls
- richer mobile diagnostics
