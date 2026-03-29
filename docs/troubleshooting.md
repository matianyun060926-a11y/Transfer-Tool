# Troubleshooting

## Safari Cannot Reach The Windows URL

- Confirm both devices are on the same Wi-Fi.
- Make sure the Windows IP shown in the app matches the current LAN IP.
- Avoid guest Wi-Fi networks that isolate devices.
- Check Windows Firewall and allow Python on private networks.

## Pairing Fails

- Refresh the pairing code in the Windows app.
- Re-enter the new code in Safari.
- Make sure pairing has not been disabled in the desktop app.

## Upload Fails

- Check that the Safari page is still open.
- Try a smaller file first.
- Watch the Diagnostics tab in the Windows app for errors.
- Confirm the receive folder shown inside the Windows app still exists and is writable.

## Download Does Not Start

- Refresh the download list in Safari.
- Make sure the Windows app still shows the shared file batch.
- If multiple files were shared, the download may be a ZIP package.

## The Wrong Windows IP Is Shown

This can happen on machines with VPNs or multiple adapters.

Try:

- disconnecting unused VPNs
- switching to the active Wi-Fi adapter
- restarting the desktop app

## History Looks Empty

- History is stored locally on Windows under `%LOCALAPPDATA%\TransferTool\transfer_history\windows_history.json`.
- Only completed transfers are written to history.
- Shared files that were prepared but not yet downloaded do not create a history entry until a download happens.

## PySide6 Is Missing

Install dependencies with:

```powershell
py -m pip install -r windows-app\requirements.txt
```

## Flask Is Missing

Install dependencies with:

```powershell
py -m pip install -r windows-app\requirements.txt
```
