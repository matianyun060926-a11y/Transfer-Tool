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

Enter the URL shown by the Windows app, for example:

`http://192.168.1.50:8765/`

### 3. Pair

Enter:

- a device name
- the 6-digit pairing code shown in the Windows app

### 4. Use the web app

You can then:

- upload files from iPhone/iPad to Windows
- download Windows-shared files to iPhone/iPad
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
2. Confirm the local IP and URL shown on the dashboard.
3. Open that URL in Safari on the phone/tablet.
4. Pair with the code.
5. Upload a small test file from Safari.
6. Confirm it appears under `runtime_data/received_files/`.
7. Share a file from Windows.
8. Download it from Safari.
9. Confirm the history list updates.
