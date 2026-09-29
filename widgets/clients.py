"""LAN cihazları paneli: IP + MAC + Hostname + cihaz başına anlık trafik."""
from __future__ import annotations

from .base import Panel, fmt_speed, COL_LABEL, COL_VALUE


class ClientsPanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__("LAN Cihazlari", **kwargs)

    def update_data(self, snap) -> None:
        devices = snap.network.lan_devices
        if not devices:
            self.update("[dim]Bagli cihaz bulunamadi.[/]")
            return

        hdr = (
            f"[bold {COL_LABEL}]{'IP':<15} {'Hostname':<13} {'D':>9} {'U':>9}[/]"
        )
        lines = [hdr]
        shown = devices[:5]
        for dev in shown:
            hostname = dev.hostname or "?"
            lines.append(
                f"{dev.ip:<15} {hostname[:13]:<13} "
                f"[{COL_VALUE}]{fmt_speed(dev.rx_rate):>9}[/] "
                f"[{COL_VALUE}]{fmt_speed(dev.tx_rate):>9}[/]"
            )
        if len(devices) > len(shown):
            lines.append(f"[dim]+{len(devices) - len(shown)} cihaz daha[/]")
        self.update("\n".join(lines))
