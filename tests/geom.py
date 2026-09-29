"""Layout geometri kontrolü: her panelin konum ve boyutunu yazdırır."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard import OpenWrtDashboard  # noqa: E402
from widgets.base import Panel  # noqa: E402

COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 100
ROWS = int(sys.argv[2]) if len(sys.argv) > 2 else 37


async def main() -> None:
    app = OpenWrtDashboard()
    async with app.run_test(size=(COLS, ROWS)) as pilot:
        await pilot.pause()
        print(f"SCREEN {COLS}x{ROWS}")
        for wid in ("header", "main-row", "left-col", "right-col", "footer"):
            try:
                w = app.query_one("#" + wid)
            except Exception:  # noqa: BLE001
                continue
            r = w.region
            print(f"  {wid:<14} x={r.x:<4} y={r.y:<4} w={r.width:<4} h={r.height}")
        print("  paneller:")
        for w in app.query(Panel):
            r = w.region
            print(f"    {str(w.id):<16} x={r.x:<4} y={r.y:<4} w={r.width:<4} h={r.height}")


if __name__ == "__main__":
    asyncio.run(main())
