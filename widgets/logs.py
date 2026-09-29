"""Sistem logları paneli: son N satır, hatalar kırmızı.

Küçük ekranda (7") satırlar SARILMASIN diye metin panel genişliğine
göre kırpılır ve yalnızca son birkaç satır gösterilir.
"""
from __future__ import annotations

import re

from .base import Panel

_TS = re.compile(r"^\w+\s+\w+\s+\d+\s+(\d+:\d+:\d+)\s+\d+\s+(.*)$")


class LogsPanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__("Sistem Loglari", **kwargs)

    def update_data(self, snap) -> None:
        if not snap.logs:
            self.update("[dim]Log kaydi yok.[/]")
            return

        width = max(20, self.size.width - 6)
        lines = []
        for entry in snap.logs[-8:]:
            txt = entry.line
            m = _TS.match(txt)
            if m:
                txt = f"{m.group(1)} {m.group(2)}"
            txt = txt.replace("[", "\\[")
            if len(txt) > width:
                txt = txt[: width - 1] + "~"
            if entry.is_error:
                lines.append(f"[bold #ff5555]{txt}[/]")
            else:
                lines.append(f"[#9fd8d2]{txt}[/]")
        self.update("\n".join(lines))
