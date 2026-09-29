"""CPU paneli: toplam + çekirdek bazında kullanım, frekans, sıcaklık, load."""
from __future__ import annotations

from .base import Panel, bar, fmt_temp, COL_LABEL, COL_VALUE


class CpuPanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__("CPU", **kwargs)

    def update_data(self, snap) -> None:
        cpu = snap.cpu
        freq = cpu.freq_mhz[0] if cpu.freq_mhz else 0
        freq_txt = f"{freq/1000:.2f} GHz" if freq else "-"
        lines = [
            f"[bold {COL_LABEL}]{'Toplam':<13}[/]{bar(cpu.total, 12)}",
            f"[{COL_LABEL}]{'Frekans:':<10}[/][bold {COL_VALUE}]{freq_txt}[/]  "
            f"[{COL_LABEL}]{'Sicaklik:':<10}[/][bold {COL_VALUE}]{fmt_temp(cpu.temp_c)}[/]",
            f"[{COL_LABEL}]{'Load:':<13}[/][dim]{cpu.load1:.2f} {cpu.load5:.2f} {cpu.load15:.2f}[/]",
        ]

        self.update("\n".join(lines))
