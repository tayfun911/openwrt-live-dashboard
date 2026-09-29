"""Geliştirme aracı: dashboard'un SVG ekran görüntüsünü üretir.

Textual'ın compositor'ını kullanarak 220x60 boyutunda render edilmiş
ekranın SVG görüntüsünü `screenshot.svg` dosyasına yazar.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard import OpenWrtDashboard  # noqa: E402


async def main() -> None:
    app = OpenWrtDashboard()
    async with app.run_test(size=(220, 60)) as pilot:
        for _ in range(3):
            app.tick()
            await pilot.pause()
        svg = app.export_screenshot(title="OpenWrt Live Dashboard")
        out = Path(__file__).resolve().parent.parent / "screenshot.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"kaydedildi: {out}")


if __name__ == "__main__":
    asyncio.run(main())
