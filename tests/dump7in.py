"""100x37 ekranın GERÇEK metnini SVG'den çıkarıp yazdırır (layout doğrulama)."""
from __future__ import annotations

import asyncio
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard import OpenWrtDashboard  # noqa: E402

COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 100
ROWS = int(sys.argv[2]) if len(sys.argv) > 2 else 37
MAXROWS = int(sys.argv[3]) if len(sys.argv) > 3 else ROWS

_TXT = re.compile(r'<text[^>]*x="([\d.]+)"[^>]*y="([\d.]+)"[^>]*>(.*?)</text>', re.S)


async def main() -> None:
    app = OpenWrtDashboard()
    async with app.run_test(size=(COLS, ROWS)) as pilot:
        for _ in range(3):
            app.tick()
            await pilot.pause()
        svg = app.export_screenshot()

    rows: dict[float, list[tuple[float, str]]] = {}
    for m in _TXT.finditer(svg):
        x, y = float(m.group(1)), float(m.group(2))
        txt = re.sub(r"<[^>]+>", "", m.group(3))
        txt = html.unescape(txt)
        rows.setdefault(y, []).append((x, txt))

    for i, y in enumerate(sorted(rows)[:MAXROWS]):
        line = "".join(t for _, t in sorted(rows[y]))
        print(f"{i:2d}|{line}")


if __name__ == "__main__":
    asyncio.run(main())
