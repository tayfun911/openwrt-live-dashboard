"""Trafik bant grafiği paneli: son N saniyelik indirme/yükleme.

Unicode blok karakterleriyle (█/░) çizilen, iki kanallı canlı grafik.
"""
from __future__ import annotations

from .base import Panel, fmt_speed, COL_LABEL, COL_VALUE


class GraphPanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__("Trafik Grafigi", **kwargs)

    def _band(self, series: list[float], color: str, height: int, width: int) -> list[str]:
        if not series:
            return ["[dim]veri bekleniyor...[/]"]
        peak = max(series) or 1.0
        # Geçmiş kısa olsa bile bandı tam genişliğe yasla (sola boşluk)
        values = [0.0] * max(0, width - len(series)) + list(series[-width:])
        rows = []
        for level in range(height, 0, -1):
            line = "".join(
                f"[{color}]█[/]" if int(v / peak * height) >= level else "[#06242c]░[/]"
                for v in values
            )
            rows.append(line)
        return rows

    def update_data(self, snap) -> None:
        net = snap.network
        rx = net.history_rx
        tx = net.history_tx

        inner = max(12, self.size.width - 8)
        height = 2

        current_rx = rx[-1] if rx else 0.0
        current_tx = tx[-1] if tx else 0.0
        lines = [
            f"[#6FB7FF]D:[/][bold {COL_VALUE}]{fmt_speed(current_rx)}[/]  "
            f"[#00FF66]U:[/][bold {COL_LABEL}]{fmt_speed(current_tx)}[/]",
        ]
        lines.extend(self._band(rx, "#6FB7FF", height, inner))
        lines.extend(self._band(tx, "#00FF66", height, inner))
        self.update("\n".join(lines))
