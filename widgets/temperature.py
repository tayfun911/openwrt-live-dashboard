"""Sıcaklık paneli: CPU + eMMC sensörleri."""
from __future__ import annotations

from .base import Panel, fmt_temp, COL_LABEL, COL_VALUE


class TemperaturePanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__("Sicakliklar", **kwargs)

    def update_data(self, snap) -> None:
        cpu = snap.cpu.temp_c
        emmc = snap.disk.emmc_temp_c
        lines = [
            f"[{COL_LABEL}]{'CPU  :':<16}[/][bold {COL_VALUE}]{fmt_temp(cpu)}[/]"
            + ("" if cpu is not None else "  [dim]yok[/]"),
            f"[{COL_LABEL}]{'eMMC :':<16}[/][bold {COL_VALUE}]{fmt_temp(emmc)}[/]"
            + ("" if emmc is not None else "  [dim]yok[/]"),
        ]
        self.update("\n".join(lines))
