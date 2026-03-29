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

    @staticmethod
    def _point_in_rounded_rect(px: int, py: int, x: int, y: int, w: int, h: int, radius: int) -> bool:
        if w <= 0 or h <= 0:
            return False
        if not (x <= px < x + w and y <= py < y + h):
            return False

        radius = max(0, min(radius, w // 2, h // 2))
        if radius == 0:
            return True

        in_middle_x = x + radius <= px < x + w - radius
        in_middle_y = y + radius <= py < y + h - radius
        if in_middle_x or in_middle_y:
            return True

        radius_sq = radius * radius
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
                return True
        return False

    def rounded_rect(self, x: int, y: int, w: int, h: int, radius: int, color: tuple[int, int, int, int]) -> None:
        for py in range(y, y + h):
            for px in range(x, x + w):
                if self._point_in_rounded_rect(px, py, x, y, w, h, radius):
                    self.set_pixel(px, py, color)

    def rounded_rect_outline(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        radius: int,
        thickness: int,
        color: tuple[int, int, int, int],
    ) -> None:
        if thickness <= 0:
            return
        inner_w = w - thickness * 2
        inner_h = h - thickness * 2
        inner_radius = max(0, radius - thickness)
        for py in range(y, y + h):
            for px in range(x, x + w):
                if not self._point_in_rounded_rect(px, py, x, y, w, h, radius):
                    continue
                if inner_w > 0 and inner_h > 0 and self._point_in_rounded_rect(
                    px,
                    py,
                    x + thickness,
                    y + thickness,
                    inner_w,
                    inner_h,
                    inner_radius,
                ):
                    continue
                self.set_pixel(px, py, color)

    def vertical_gradient_rounded_rect(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        radius: int,
        start: tuple[int, int, int, int],
        end: tuple[int, int, int, int],
    ) -> None:
        for py in range(y, y + h):
            t = (py - y) / max(1, h - 1)
            row_rgb = interpolate(start[:3], end[:3], t)
            row_alpha = int(start[3] + (end[3] - start[3]) * t)
            row_color = (*row_rgb, row_alpha)
            for px in range(x, x + w):
                if self._point_in_rounded_rect(px, py, x, y, w, h, radius):
                    self.set_pixel(px, py, row_color)

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
    canvas.fill((0, 0, 0, 0))

    parchment = (251, 245, 238, 255)
    warm_sand = (244, 238, 231, 255)
    soft_linen = (234, 220, 205, 255)
    border = (231, 219, 207, 255)
    espresso = (54, 42, 34, 255)
    stone = (143, 114, 88, 235)
    caramel = (209, 174, 137, 245)
    terracotta = (203, 116, 94, 255)
    shadow = (108, 81, 58, 28)

    tile_margin = int(size * 0.08)
    tile_x = tile_margin
    tile_y = tile_margin
    tile_size = size - tile_margin * 2
    tile_radius = int(size * 0.22)

    for index in range(3):
        expand = 3 - index
        alpha = shadow[3] - index * 7
        canvas.rounded_rect(
            tile_x + int(size * 0.012),
            tile_y + int(size * 0.022) + index,
            tile_size,
            tile_size,
            tile_radius + expand,
            (shadow[0], shadow[1], shadow[2], max(alpha, 0)),
        )

    canvas.vertical_gradient_rounded_rect(tile_x, tile_y, tile_size, tile_size, tile_radius, parchment, soft_linen)
    canvas.rounded_rect_outline(tile_x, tile_y, tile_size, tile_size, tile_radius, max(1, int(size * 0.012)), border)
    canvas.vertical_gradient_rounded_rect(
        tile_x + int(size * 0.018),
        tile_y + int(size * 0.018),
        tile_size - int(size * 0.036),
        tile_size - int(size * 0.036),
        max(0, tile_radius - int(size * 0.018)),
        (255, 252, 249, 80),
        (255, 255, 255, 0),
    )

    frame_radius = int(size * 0.06)
    frame_thickness = max(2, int(size * 0.024))

    front_x = int(size * 0.29)
    front_y = int(size * 0.31)
    front_size = int(size * 0.30)
    back_x = int(size * 0.47)
    back_y = int(size * 0.22)
    back_size = int(size * 0.23)

    canvas.rounded_rect_outline(front_x, front_y, front_size, front_size, frame_radius, frame_thickness, espresso)
    canvas.rounded_rect_outline(back_x, back_y, back_size, back_size, frame_radius, frame_thickness, stone)

    line_thickness = max(3, int(size * 0.03))
    line_start_x = int(size * 0.43)
    line_start_y = int(size * 0.58)
    line_end_x = int(size * 0.66)
    line_end_y = int(size * 0.35)
    canvas.line(line_start_x, line_start_y, line_end_x, line_end_y, line_thickness, terracotta)
    canvas.circle(line_end_x, line_end_y, max(4, int(size * 0.015)), caramel)

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
