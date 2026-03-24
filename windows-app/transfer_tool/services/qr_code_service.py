from __future__ import annotations

import io

import qrcode


def build_qr_png_bytes(text: str) -> bytes:
    qr = qrcode.QRCode(border=2, box_size=6)
    qr.add_data(text)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#2e6d77", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
