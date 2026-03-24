from transfer_tool.services.qr_code_service import build_qr_png_bytes


def test_qr_code_service_returns_png_bytes() -> None:
    payload = build_qr_png_bytes("http://127.0.0.1:8765/")

    assert payload.startswith(b"\x89PNG\r\n\x1a\n")
