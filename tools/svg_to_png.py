"""Convert a Textual/Rich SVG screenshot into a pixel-accurate PNG.

Why this exists
---------------
`App.export_screenshot()` only produces SVG. Rich embeds *Fira Code* through a
CSS ``@font-face`` that points at a CDN. When such an SVG is embedded in a
README (``<img src="...svg">``) browsers refuse to load the external webfont,
so the SVG falls back to whatever monospace font is available. Block and box
drawing glyphs (``█ ░ ─ │ ┌ ┐ └ ┘``) then get different advance widths and the
layout visibly falls apart - the logo looks broken and panel borders no longer
line up.

This converter rasterises the SVG itself:

* every cell is painted from the ``<rect ... shape-rendering="crispEdges">``
  background rectangles,
* block characters (``█ ▒ ▓ ░``) are drawn as filled rectangles instead of
  glyphs,
* box drawing characters (``─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼`` and the rounded variants)
  are drawn as line segments that span the full cell, so borders tile
  seamlessly,
* everything else is rendered with a real monospace font.

The result is deterministic and looks the same everywhere.

Usage
-----
    python tools/svg_to_png.py screenshot.svg screenshot.png
    python tools/svg_to_png.py screenshot.svg out.png --scale 3 --font C:/Windows/Fonts/consola.ttf
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

# ----------------------------------------------------------------------
#  Regexes for the Rich SVG dialect
# ----------------------------------------------------------------------
_STYLE_RULE = re.compile(r"\.([\w-]+)\s*\{([^}]*)\}")
_FILL = re.compile(r"fill:\s*(#[0-9a-fA-F]{3,8})")
_FONT_SIZE = re.compile(r"font-size:\s*([\d.]+)px")
_TRANSLATE = re.compile(r'<g transform="translate\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)"')
_LINE_DEF = re.compile(
    r'id="[\w-]+-line-(\d+)">\s*<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"'
)
_BG_RECT = re.compile(
    r'<rect fill="(#[0-9a-fA-F]{6})" x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"'
    r' shape-rendering="crispEdges"'
)
_TEXT = re.compile(
    r'<text class="([\w-]+)" x="([\d.]+)" y="([\d.]+)" textLength="([\d.]+)"'
    r'[^>]*clip-path="url\(#[^)]*-line-(\d+)\)"[^>]*>(.*?)</text>',
    re.S,
)
_INNER_TAG = re.compile(r"<[^>]+>")

# ----------------------------------------------------------------------
#  Character tables
# ----------------------------------------------------------------------
#: Block elements -> fraction of the cell that gets filled.
BLOCKS = {
    "\u2588": 1.0,   # █
    "\u2593": 0.72,  # ▓
    "\u2592": 0.45,  # ▒
    "\u2591": 0.22,  # ░
}

#: Box drawing -> (left, right, up, down) connections.
BOX = {
    "\u2500": (1, 1, 0, 0),  # ─
    "\u2502": (0, 0, 1, 1),  # │
    "\u250c": (0, 1, 0, 1),  # ┌
    "\u2510": (1, 0, 0, 1),  # ┐
    "\u2514": (0, 1, 1, 0),  # └
    "\u2518": (1, 0, 1, 0),  # ┘
    "\u251c": (0, 1, 1, 1),  # ├
    "\u2524": (1, 0, 1, 1),  # ┤
    "\u252c": (1, 1, 0, 1),  # ┬
    "\u2534": (1, 1, 1, 0),  # ┴
    "\u253c": (1, 1, 1, 1),  # ┼
    "\u2550": (1, 1, 0, 0),  # ═
    "\u2551": (0, 0, 1, 1),  # ║
    "\u256d": (0, 1, 0, 1),  # ╭
    "\u256e": (1, 0, 0, 1),  # ╮
    "\u2570": (0, 1, 1, 0),  # ╰
    "\u256f": (1, 0, 1, 0),  # ╯
}

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\CascadiaMono.ttf",
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\lucon.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/Library/Fonts/DejaVu Sans Mono.ttf",
]


# ----------------------------------------------------------------------
#  Parsing
# ----------------------------------------------------------------------
def _parse_colors(svg: str) -> dict[str, tuple[str, bool]]:
    """Map a CSS class name to ``(color, is_bold)``."""
    colors: dict[str, tuple[str, bool]] = {}
    for cls, body in _STYLE_RULE.findall(svg):
        m = _FILL.search(body)
        if not m:
            continue
        colors[cls] = (m.group(1).lower(), "bold" in body)
    return colors


def _parse_grid(svg: str):
    """Return ``(cells, rows, cols, cell_w, cell_h)``.

    ``cells[row][col]`` is ``(char, color, bold, background)``.
    """
    font_size = float(_FONT_SIZE.search(svg).group(1))

    # Row index -> y offset, taken from the per-line clip paths.
    line_y: dict[float, int] = {}
    for row, _x, y, _w, _h in _LINE_DEF.findall(svg):
        line_y[round(float(y), 1)] = int(row)
    rows = len(line_y)
    ys = sorted(line_y)
    cell_h = round(ys[1] - ys[0], 2) if rows > 1 else font_size * 1.22
    y0 = ys[0] if ys else 0.0

    # The matrix group starts here; the window title markup lives before it.
    m = _TRANSLATE.search(svg)
    body = svg[m.end() :] if m else svg

    x_start = float(m.group(1)) if m else 0.0
    y_start = float(m.group(2)) if m else 0.0

    colors = _parse_colors(svg)

    # Cell width: the smallest horizontal distance between two text anchors.
    xs = sorted({float(x) for _c, x, _y, _l, _r, _t in _TEXT.findall(body)})
    gaps = [b - a for a, b in zip(xs, xs[1:]) if b - a > 0.5]
    cell_w = round(min(gaps), 2) if gaps else round(font_size * 0.61, 2)

    # Background grid.
    grid: dict[int, dict[int, str]] = {}
    cols = 0
    for fill, rx, ry, rw, rh in _BG_RECT.findall(body):
        row = line_y.get(round(float(ry) - y_start + y0, 1))
        if row is None:
            continue
        c0 = int(round((float(rx) - x_start) / cell_w))
        c1 = int(round((float(rx) + float(rw) - x_start) / cell_w))
        for col in range(max(0, c0), c1):
            grid.setdefault(row, {})[col] = fill.lower()
            cols = max(cols, col + 1)

    # Text runs.
    cells: dict[tuple[int, int], tuple[str, str, bool]] = {}
    for cls, x, _y, _len, row, raw in _TEXT.findall(body):
        color, bold = colors.get(cls, ("#c5c8c6", False))
        text = html.unescape(_INNER_TAG.sub("", raw)).replace("\u00a0", " ")
        col = int(round((float(x) - x_start) / cell_w))
        for offset, ch in enumerate(text):
            if ch in "\r\n":
                continue
            cells[(int(row), col + offset)] = (ch, color, bold)
            cols = max(cols, col + offset + 1)

    return cells, grid, rows, cols, cell_w, cell_h


# ----------------------------------------------------------------------
#  Rendering
# ----------------------------------------------------------------------
def _mix(fg: str, bg: str, alpha: float) -> tuple[int, int, int]:
    """Alpha-blend two ``#rrggbb`` colours."""
    f = tuple(int(fg[i : i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(bg[i : i + 2], 16) for i in (1, 3, 5))
    return tuple(round(f[i] * alpha + b[i] * (1 - alpha)) for i in range(3))  # type: ignore[return-value]


def _find_font(explicit: str | None) -> str | None:
    if explicit:
        return explicit if Path(explicit).exists() else None
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def svg_to_png(
    svg: str,
    out_path: str | Path,
    scale: float = 2.0,
    font_path: str | None = None,
) -> Path:
    """Rasterise a Rich/Textual SVG screenshot and write it to ``out_path``."""
    from PIL import Image, ImageDraw, ImageFont

    cells, grid, rows, cols, cell_w, cell_h = _parse_grid(svg)

    cw = max(1, round(cell_w * scale))
    ch = max(1, round(cell_h * scale))
    img = Image.new("RGB", (cols * cw, rows * ch), (0, 10, 16))
    draw = ImageDraw.Draw(img)

    # 1) backgrounds
    for row in range(rows):
        for col, fill in grid.get(row, {}).items():
            draw.rectangle(
                [col * cw, row * ch, (col + 1) * cw - 1, (row + 1) * ch - 1], fill=fill
            )

    # 2) text
    resolved = _find_font(font_path)
    font = None
    if resolved:
        font = ImageFont.truetype(resolved, max(6, round(cell_h * scale * 0.78)))

    thickness = max(1, round(ch * 0.08))
    for (row, col), (char, color, bold) in cells.items():
        x, y = col * cw, row * ch
        background = grid.get(row, {}).get(col, "#000a10")

        if char == " ":
            continue

        # --- block elements: filled rectangle (guaranteed tiling) ---
        if char in BLOCKS:
            alpha = BLOCKS[char]
            if alpha >= 1.0:
                draw.rectangle([x, y, x + cw - 1, y + ch - 1], fill=color)
            else:
                draw.rectangle(
                    [x, y, x + cw - 1, y + ch - 1],
                    fill=_mix(color, background, alpha),
                )
            continue

        # --- box drawing: line segments that span the full cell ---
        if char in BOX:
            left, right, up, down = BOX[char]
            mid_x = x + cw // 2
            mid_y = y + ch // 2
            half = thickness // 2
            if left or right:
                x0 = x if left else mid_x
                x1 = x + cw if right else mid_x
                draw.rectangle([x0, mid_y - half, x1 - 1, mid_y - half + thickness - 1], fill=color)
            if up or down:
                y0 = y if up else mid_y
                y1 = y + ch if down else mid_y
                draw.rectangle([mid_x - half, y0, mid_x - half + thickness - 1, y1 - 1], fill=color)
            continue

        # --- everything else: real glyph, centred inside its cell ---
        if font is not None:
            draw.text(
                (x + cw / 2, y + ch / 2),
                char,
                font=font,
                fill=color,
                anchor="mm",
                stroke_width=1 if bold else 0,
                stroke_fill=color,
            )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path, help="input .svg file")
    parser.add_argument("png", type=Path, help="output .png file")
    parser.add_argument("--scale", type=float, default=2.0, help="pixel scale (default: 2)")
    parser.add_argument("--font", default=None, help="path to a monospace .ttf")
    args = parser.parse_args()

    path = svg_to_png(args.svg.read_text(encoding="utf-8"), args.png, args.scale, args.font)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
