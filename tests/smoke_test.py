"""Kurulum sonrası hızlı doğrulama.

Uygulamayı Textual'ın test modunda başlatır, birkaç veri turu işler ve
panellerin hatasız render edildiğini kontrol eder.

Çalıştırma:
    pip install textual
    python tests/smoke_test.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard import OpenWrtDashboard  # noqa: E402


async def main() -> None:
    app = OpenWrtDashboard()
    async with app.run_test(size=(200, 55)) as pilot:
        for _ in range(4):
            app.tick()
            await pilot.pause()
        # Yardım ekranını da açıp kapatmayı dene
        await pilot.press("f1")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        print("SMOKE TEST OK")


if __name__ == "__main__":
    asyncio.run(main())
