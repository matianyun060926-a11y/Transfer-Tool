# Manual Test Checklist

## Basic Setup

- Windows app starts successfully.
- The dashboard shows a local IP, URL, port, and pairing code.
- The `runtime_data/` folders are created locally.

## Pairing

- Safari can open the Windows URL.
- Correct pairing code succeeds.
- Incorrect pairing code fails with a useful message.
- Refreshing the pairing code invalidates the old code.

## Uploads From iPhone/iPad To Windows

- Upload one small file.
- Upload multiple files.
- Upload files with the same name across different attempts.
- Confirm files are saved under `runtime_data/received_files/`.
- Confirm history shows an incoming success entry.

## Downloads From Windows To iPhone/iPad

- Share one file from Windows.
- Download that file from Safari.
- Share multiple files from Windows.
- Download the generated ZIP package from Safari.
- Confirm history shows an outgoing success entry.

## Desktop UI

- Device name can be edited and saved.
- Pairing code can be refreshed.
- Pairing can be disabled.
- A shared file batch can be removed.
- Diagnostics log updates during use.

## Failure Cases

- Try opening the Safari page while the Windows app is closed.
- Try using an expired pairing code.
- Interrupt Wi-Fi during an upload.
- Remove a shared batch and confirm it disappears from Safari after refresh.

## What Works Now

- hosted Windows local server
- Safari mobile UI
- file uploads to Windows
- file downloads from Windows
- recent history
- simple pairing

## Simplified In This MVP

- no discovery
- no background mobile transfers
- no resume support
- no QR code helper yet
