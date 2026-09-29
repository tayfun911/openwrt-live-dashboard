"""Geliştirme aracı: her panelin render edilen metnini yazdırır.

Textual'ın test modunda uygulamayı başlatır, bir veri turu işler ve her
panelStatic'inin içeriğini konsola döker — düzenin bozuk olup olmadığını
gözle kontrol etmek için kullanışlıdır.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.text import Text  # noqa: E402
from textual.widgets import Static  # noqa: E402

from dashboard import OpenWrtDashboard  # noqa: E402


async def main() -> None:
    app = OpenWrtDashboard()
    async with app.run_test(size=(200, 55)) as pilot:
        app.tick()
        await pilot.pause()
        print("=" * 90)
        for panel in app.query(".panel"):
            print(f"\n### {panel.id or panel.__class__.__name__}")
            children = list(panel.query(Static))
            for child in children:
                content = getattr(child, "content", None)
                if content is None:
                    continue
                if isinstance(content, Text):
                    print(content.plain)
                else:
                    print(content)
            if not children:
                content = getattr(panel, "content", None)
                if isinstance(content, Text):
                    print(content.plain)
                else:
                    print(content)
        print("\n" + "=" * 90)


if __name__ == "__main__":
    asyncio.run(main())
