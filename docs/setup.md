# Setup

## Windows Setup

### 1. Install Python

Install Python 3.13 or newer.

Verify:

```powershell
py --version
```

### 2. Create a virtual environment

From the repo root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
py -m pip install -r windows-app\requirements.txt
```

### 4. Run the desktop app

From the repo root:

```powershell
py windows-app\main.py
```

Or use the launcher batch file:

```powershell
windows-app\launch_transfer_tool.bat
```

### 5. Allow local network access

If Windows Firewall prompts you:

- allow Python on private networks
- keep the app on trusted home LANs only

## iPhone / iPad Setup

No native app install is needed.

### 1. Connect to the same Wi-Fi as the Windows PC

The phone/tablet and Windows PC must be on the same LAN.

### 2. Open Safari

Use either of these:

- scan the QR code shown in the Windows app to open Safari and finish one-time trusted pairing automatically
- or enter the URL shown by the Windows app, for example:

`http://192.168.1.50:8765/`

### 3. Pair

If you used the QR code, Safari should trust the device automatically.

If you opened the URL manually, enter:

- a device name
- the 6-digit pairing code shown in the Windows app

### 4. Use the web app

You can then:

- upload files from iPhone/iPad to Windows
- download Windows-shared files to iPhone/iPad
- reopen later in the same Safari browser without re-pairing for about 30 days unless trust is revoked or storage is cleared
- retry a failed upload or download
- cancel the current upload or download
- refresh recent transfer history

## Optional Home Screen Setup

For a more app-like feel on iPhone/iPad:

1. Open the tool in Safari.
2. Tap the Share button.
3. Tap `Add to Home Screen`.

## Desktop Shortcut

Shortcuts are now secondary.

The preferred shared-distribution flow is:

1. build the packaged app folder
2. open the packaged folder
3. click `TransferTool.exe`

An additional portable launcher batch file is also generated in that folder:

`Open Transfer Tool.bat`

### Optional PowerShell shortcut script

You can also create the shortcut manually with:

```powershell
powershell -ExecutionPolicy Bypass -File windows-app\scripts\create_desktop_shortcut.ps1
```

If a packaged executable exists at `dist\TransferTool\TransferTool.exe`, the script targets that executable automatically.

## Local Testing Flow

1. Start the Windows app.
2. Confirm the local IP, URL, QR code, pairing code, and receive folder are shown on the dashboard.
3. Scan the QR code from iPhone/iPad and confirm Safari opens the page already trusted without typing the code.
4. Close Safari, reopen the same page later in the same browser, and confirm it restores access automatically without asking for the code again.
5. In the Windows app, confirm the trusted device appears in the trusted devices list.
6. Select that device in the Windows app and click `Revoke Selected`.
7. Reload Safari and confirm it asks for pairing again.
8. Go to `Shared Files` and drag one or more files into the drop zone.
9. Confirm the files appear in the shared list immediately.
10. Click the same drop zone and confirm it opens the file picker.
11. Upload a small test file from Safari and confirm it appears under `runtime_data/received_files/`.
12. Hover over the receive folder path in the Windows app and confirm the full path is available.
13. Click `Copy Path` and confirm the full receive path is copied.
14. Start another upload or download, then use Cancel in Safari while it is in progress.
15. Confirm the transfer card shows the cancellation state.
16. Use Retry and confirm the transfer can be started again.
