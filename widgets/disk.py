"""Disk paneli: root doluluk oranı."""
from __future__ import annotations

from .base import Panel, bar, COL_LABEL, COL_VALUE


class DiskPanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__("Disk (Root)", **kwargs)

    def update_data(self, snap) -> None:
        disk = snap.disk
        lines = [
            f"[{COL_LABEL}]{'Root:':<13}[/]{bar(disk.root_pct, 12)}",
            f"[{COL_LABEL}]{'Kullanim:':<13}[/][bold {COL_VALUE}]{disk.root_used_mb} MB[/] / {disk.root_total_mb} MB",
        ]
        self.update("\n".join(lines))
