# Architecture

## Overview

This project uses one Windows PC as the single local host.

- The Windows desktop app is the main control center.
- The Windows app runs a Flask local server on the LAN.
- Safari on iPhone/iPad connects to that server using the Windows PC local IP and port.
- The mobile UI is a static web app served directly by the Windows PC.

This is simpler than a native iOS app because:

- there is no Apple build pipeline
- there is no Xcode dependency
- the phone does not need to run its own local server
- the Windows machine stays the single source of truth

## Main Flow

### Upload from iPhone/iPad to Windows

1. Windows app starts the local server.
2. Windows app shows a local URL and pairing code.
3. Safari opens the URL.
4. Mobile user enters the pairing code.
5. The web app uploads files to the Windows server.
6. Windows saves them into `runtime_data/received_files/`.
7. A history entry is written to JSON.

### Download from Windows to iPhone/iPad

1. Windows user chooses one or more files to share.
2. The app copies those files into runtime-managed share storage.
3. If there are multiple files, the app creates a ZIP package.
4. The paired mobile web UI lists the available download packages.
5. Safari downloads the selected file or ZIP package.
6. A history entry is written to JSON on Windows.

## Beginner-Friendly Module Map

### Windows app

- `windows-app/main.py`
  Starts the desktop app.

- `windows-app/transfer_tool/ui/app_state.py`
  Connects the desktop UI to the services and the web server.

- `windows-app/transfer_tool/ui/main_window.py`
  The PySide6 desktop window. It shows pairing info, shared files, history, and logs.

- `windows-app/transfer_tool/networking/http_server.py`
  Flask server that serves the mobile web UI and the upload/download APIs.

- `windows-app/transfer_tool/services/file_store.py`
  Creates receive folders and safely names uploaded files.

- `windows-app/transfer_tool/services/share_store.py`
  Copies Windows-selected files into runtime share storage and builds ZIP downloads when needed.

- `windows-app/transfer_tool/services/web_transfer_service.py`
  High-level logic for uploads, downloads, share creation, and history updates.

- `windows-app/transfer_tool/services/history_store.py`
  Saves the last 20 transfer records into a local JSON file.

- `windows-app/transfer_tool/services/pairing.py`
  Generates the 6-digit pairing code and short-lived browser sessions.

### Mobile web app

- `web-app/index.html`
  The mobile page structure.

- `web-app/assets/styles.css`
  The mobile-friendly visual layout.

- `web-app/assets/app.js`
  Pairing, upload, download, history refresh, and progress behavior in Safari.

## Storage

Windows runtime storage lives under `runtime_data/`:

- `runtime_data/received_files/`
  Files uploaded from iPhone/iPad.

- `runtime_data/shared_files/`
  Runtime-managed copies of Windows files that are made available for mobile download.

- `runtime_data/transfer_history/`
  JSON history and share manifests.

- `runtime_data/logs/`
  Log files for diagnostics.

## Why This Is The Simplest Useful Design

- only one machine hosts the protocol
- only one local server is needed
- Safari is enough on iPhone/iPad
- pairing is local and understandable
- JSON is enough for settings and history
- runtime files stay out of Git
