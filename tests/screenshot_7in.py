"""7 inç (800x600) ekran için geliştirme aracı: SVG ekran görüntüsü üretir.

800x600 framebuffer + 8x16 konsol fontu ~ 100 sütun x 37 satır eder.
Bu boyutta layout'un nasıl göründüğünü kontrol etmek için kullanılır.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard import OpenWrtDashboard  # noqa: E402

COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 100
ROWS = int(sys.argv[2]) if len(sys.argv) > 2 else 37


async def main() -> None:
    app = OpenWrtDashboard()
    async with app.run_test(size=(COLS, ROWS)) as pilot:
        for _ in range(3):
            app.tick()
            await pilot.pause()
        svg = app.export_screenshot(title="OpenWrt 7in")
        out = Path(__file__).resolve().parent.parent / "screenshot_7in.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"kaydedildi: {out} ({COLS}x{ROWS})")


if __name__ == "__main__":
    asyncio.run(main())
