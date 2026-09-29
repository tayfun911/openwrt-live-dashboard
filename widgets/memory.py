"""Bellek paneli: RAM kullanımı, cache, buffer."""
from __future__ import annotations

from .base import Panel, bar, COL_LABEL, COL_VALUE


class MemoryPanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__("Bellek (RAM)", **kwargs)

    def update_data(self, snap) -> None:
        mem = snap.memory
        lines = [
            f"[bold {COL_LABEL}]{'Kullanim:':<13}[/]{bar(mem.pct, 12)}",
            f"[{COL_LABEL}]{'Kullanilan:':<13}[/][bold {COL_VALUE}]{mem.used_mb} MB[/] / {mem.total_mb} MB",
            f"[{COL_LABEL}]{'Bosta:':<13}[/][bold {COL_VALUE}]{mem.available_mb} MB[/]",
        ]
        self.update("\n".join(lines))
