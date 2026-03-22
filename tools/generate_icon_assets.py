from __future__ import annotations

import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WINDOWS_RESOURCES = ROOT / "windows-app" / "resources"
WEB_ROOT = ROOT / "web-app"


def blend(src: tuple[int, int, int, int], dst: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    sr, sg, sb, sa = src
    dr, dg, db, da = dst
    alpha = sa / 255
    inv = 1 - alpha
    out_a = min(255, int(sa + da * inv))
    if out_a == 0:
        return (0, 0, 0, 0)
    out_r = int(sr * alpha + dr * inv)
    out_g = int(sg * alpha + dg * inv)
    out_b = int(sb * alpha + db * inv)
    return (out_r, out_g, out_b, out_a)


class Canvas:
    def __init__(self, size: int) -> None:
        self.size = size
        self.pixels = [(0, 0, 0, 0)] * (size * size)

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int, int]) -> None:
        if 0 <= x < self.size and 0 <= y < self.size:
            index = y * self.size + x
            self.pixels[index] = blend(color, self.pixels[index])

    def fill(self, color: tuple[int, int, int, int]) -> None:
        self.pixels = [color] * (self.size * self.size)

    def rounded_rect(self, x: int, y: int, w: int, h: int, radius: int, color: tuple[int, int, int, int]) -> None:
        radius_sq = radius * radius
        for py in range(y, y + h):
            for px in range(x, x + w):
                in_middle_x = x + radius <= px < x + w - radius
                in_middle_y = y + radius <= py < y + h - radius
                if in_middle_x or in_middle_y:
                    self.set_pixel(px, py, color)
                    continue
                corners = (
                    (x + radius, y + radius),
                    (x + w - radius - 1, y + radius),
                    (x + radius, y + h - radius - 1),
                    (x + w - radius - 1, y + h - radius - 1),
                )
                for cx, cy in corners:
                    dx = px - cx
                    dy = py - cy
                    if dx * dx + dy * dy <= radius_sq:
                        self.set_pixel(px, py, color)
                        break

    def line(self, x1: int, y1: int, x2: int, y2: int, thickness: int, color: tuple[int, int, int, int]) -> None:
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        radius = max(1, thickness // 2)
        for step in range(steps + 1):
            t = step / steps
            x = int(round(x1 + (x2 - x1) * t))
            y = int(round(y1 + (y2 - y1) * t))
            self.circle(x, y, radius, color)

    def circle(self, cx: int, cy: int, radius: int, color: tuple[int, int, int, int]) -> None:
        radius_sq = radius * radius
        for py in range(cy - radius, cy + radius + 1):
            for px in range(cx - radius, cx + radius + 1):
                dx = px - cx
                dy = py - cy
                if dx * dx + dy * dy <= radius_sq:
                    self.set_pixel(px, py, color)

    def triangle(self, p1, p2, p3, color) -> None:
        min_x = max(0, min(p1[0], p2[0], p3[0]))
        max_x = min(self.size - 1, max(p1[0], p2[0], p3[0]))
        min_y = max(0, min(p1[1], p2[1], p3[1]))
        max_y = min(self.size - 1, max(p1[1], p2[1], p3[1]))

        def area(a, b, c):
            return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

        full = area(p1, p2, p3)
        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                p = (px, py)
                a1 = area(p, p2, p3)
                a2 = area(p1, p, p3)
                a3 = area(p1, p2, p)
                if (a1 >= 0 and a2 >= 0 and a3 >= 0 and full >= 0) or (a1 <= 0 and a2 <= 0 and a3 <= 0 and full <= 0):
                    self.set_pixel(px, py, color)

    def to_png_bytes(self) -> bytes:
        width = self.size
        height = self.size
        raw = bytearray()
        for y in range(height):
            raw.append(0)
            for x in range(width):
                raw.extend(self.pixels[y * width + x])

        def chunk(tag: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
        return b"".join(
            [
                b"\x89PNG\r\n\x1a\n",
                chunk(b"IHDR", ihdr),
                chunk(b"IDAT", zlib.compress(bytes(raw), 9)),
                chunk(b"IEND", b""),
            ]
        )


def interpolate(start: tuple[int, int, int], end: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(start[index] + (end[index] - start[index]) * t) for index in range(3))


def draw_icon(size: int) -> Canvas:
    canvas = Canvas(size)
    charcoal = (8, 17, 22, 255)
    canvas.fill((0, 0, 0, 0))

    for y in range(size):
        for x in range(size):
            distance = min(1.0, ((x - size * 0.18) ** 2 + (y - size * 0.15) ** 2) ** 0.5 / (size * 0.92))
            bg = interpolate((20, 46, 56), (7, 16, 22), distance)
            canvas.set_pixel(x, y, (*bg, 255))

    outer_margin = int(size * 0.07)
    inner_margin = int(size * 0.13)
    canvas.rounded_rect(outer_margin, outer_margin, size - outer_margin * 2, size - outer_margin * 2, int(size * 0.22), (12, 25, 32, 255))
    canvas.rounded_rect(inner_margin, inner_margin, size - inner_margin * 2, size - inner_margin * 2, int(size * 0.18), (14, 27, 35, 255))

    accent_a = (52, 228, 218, 255)
    accent_b = (31, 142, 178, 255)
    muted_line = (30, 57, 68, 255)
    screen_dark = charcoal
    paper = (232, 248, 255, 255)

    def paint_gradient_rect(x, y, w, h, radius):
        for py in range(y, y + h):
            t = (py - y) / max(1, h - 1)
            row_color = (*interpolate(accent_a[:3], accent_b[:3], t), 255)
            canvas.rounded_rect(x, py, w, 1, radius if py in {y, y + h - 1} else 0, row_color)

    left_x = int(size * 0.18)
    left_y = int(size * 0.32)
    left_w = int(size * 0.38)
    left_h = int(size * 0.25)
    paint_gradient_rect(left_x, left_y, left_w, left_h, int(size * 0.05))
    canvas.rounded_rect(left_x + int(size * 0.03), left_y + int(size * 0.03), left_w - int(size * 0.06), left_h - int(size * 0.06), int(size * 0.03), screen_dark)
    canvas.rounded_rect(int(size * 0.32), int(size * 0.58), int(size * 0.11), int(size * 0.035), int(size * 0.015), accent_a)
    canvas.rounded_rect(int(size * 0.28), int(size * 0.62), int(size * 0.19), int(size * 0.035), int(size * 0.015), muted_line)

    phone_x = int(size * 0.62)
    phone_y = int(size * 0.23)
    phone_w = int(size * 0.18)
    phone_h = int(size * 0.34)
    paint_gradient_rect(phone_x, phone_y, phone_w, phone_h, int(size * 0.05))
    canvas.rounded_rect(phone_x + int(size * 0.028), phone_y + int(size * 0.03), phone_w - int(size * 0.056), phone_h - int(size * 0.06), int(size * 0.03), screen_dark)
    canvas.rounded_rect(phone_x + int(size * 0.08), phone_y + int(size * 0.27), int(size * 0.03), int(size * 0.01), int(size * 0.005), accent_a)

    canvas.line(int(size * 0.5), int(size * 0.42), int(size * 0.66), int(size * 0.34), int(size * 0.045), (123, 239, 231, 255))
    canvas.triangle(
        (int(size * 0.70), int(size * 0.30)),
        (int(size * 0.78), int(size * 0.34)),
        (int(size * 0.72), int(size * 0.41)),
        (123, 239, 231, 255),
    )

    doc_x = int(size * 0.42)
    doc_y = int(size * 0.50)
    doc_w = int(size * 0.17)
    doc_h = int(size * 0.21)
    canvas.rounded_rect(doc_x, doc_y, doc_w, doc_h, int(size * 0.035), paper)
    canvas.line(doc_x + int(size * 0.11), doc_y, doc_x + doc_w, doc_y + int(size * 0.09), int(size * 0.012), accent_b)
    canvas.rounded_rect(doc_x + int(size * 0.035), doc_y + int(size * 0.11), int(size * 0.10), int(size * 0.018), int(size * 0.008), accent_b)
    canvas.rounded_rect(doc_x + int(size * 0.035), doc_y + int(size * 0.16), int(size * 0.075), int(size * 0.018), int(size * 0.008), (32, 154, 192, 255))

    return canvas


def resize_nearest(source: Canvas, size: int) -> Canvas:
    target = Canvas(size)
    for y in range(size):
        for x in range(size):
            src_x = int(x * source.size / size)
            src_y = int(y * source.size / size)
            target.set_pixel(x, y, source.pixels[src_y * source.size + src_x])
    return target


def write_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_ico(path: Path, png_images: list[tuple[int, bytes]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = struct.pack("<HHH", 0, 1, len(png_images))
    entries = bytearray()
    offset = 6 + len(png_images) * 16
    image_blobs = bytearray()
    for size, blob in png_images:
        width_byte = 0 if size >= 256 else size
        height_byte = 0 if size >= 256 else size
        entries.extend(struct.pack("<BBBBHHII", width_byte, height_byte, 0, 0, 1, 32, len(blob), offset))
        image_blobs.extend(blob)
        offset += len(blob)
    path.write_bytes(header + bytes(entries) + bytes(image_blobs))


def main() -> None:
    base = draw_icon(512)
    png_512 = base.to_png_bytes()
    png_256 = resize_nearest(base, 256).to_png_bytes()
    png_192 = resize_nearest(base, 192).to_png_bytes()
    png_180 = resize_nearest(base, 180).to_png_bytes()
    png_64 = resize_nearest(base, 64).to_png_bytes()

    write_file(WINDOWS_RESOURCES / "transfer-tool.png", png_256)
    write_ico(WINDOWS_RESOURCES / "transfer-tool.ico", [(256, png_256), (64, png_64)])

    write_file(WEB_ROOT / "icon-512.png", png_512)
    write_file(WEB_ROOT / "icon-192.png", png_192)
    write_file(WEB_ROOT / "apple-touch-icon.png", png_180)
    write_file(WEB_ROOT / "favicon.png", png_64)
    write_ico(WEB_ROOT / "favicon.ico", [(64, png_64)])


if __name__ == "__main__":
    main()
