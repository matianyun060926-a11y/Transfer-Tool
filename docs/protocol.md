# Protocol

## Base URL

The Windows app hosts the local server on:

`http://<windows-lan-ip>:8765/`

The port comes from app settings and defaults to `8765`.

## Pairing Model

- The Windows app generates a 6-digit pairing code.
- Safari sends the code to the Windows server.
- If the code matches and has not expired, the server returns a short-lived session token.
- Protected API calls include the token in the `X-Session-Token` header.

## Endpoints

### `GET /`

Serves the mobile web UI.

### `GET /api/device`

Returns local server metadata:

- Windows device name
- platform label
- app version
- whether pairing is enabled
- hosted mobile URL

### `POST /api/pair`

Body:

```json
{
  "sender_device_id": "mobile-abc123",
  "sender_device_name": "Matt's iPhone",
  "pairing_code": "123456"
}
```

Returns:

```json
{
  "session_token": "token",
  "expires_at": "timestamp"
}
```

### `GET /api/history`

Requires `X-Session-Token`.

Returns the recent history list from the Windows JSON history store.

### `GET /api/shares`

Requires `X-Session-Token`.

Returns the currently available Windows-side shared download packages.

### `POST /api/uploads`

Requires `X-Session-Token`.

Accepts multipart form data with one or more `files` fields.

The server saves the uploads into a batch folder under `runtime_data/received_files/`.

### `GET /api/downloads/<share_id>`

Requires `X-Session-Token`.

Returns:

- a single file if the share contains one file
- a ZIP package if the share contains multiple files

## Progress

- Upload progress is tracked in Safari with `XMLHttpRequest.upload.onprogress`.
- Download progress is tracked in Safari with `XMLHttpRequest.onprogress`.
- Desktop activity is shown in the PySide window and logs.
