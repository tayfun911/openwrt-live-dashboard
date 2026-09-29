"""Güvenlik paneli: firewall, conntrack, DNS sorgu sayısı, AdGuard Home."""
from __future__ import annotations

from .base import Panel, COL_LABEL, COL_VALUE


class FirewallPanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__("Guvenlik", **kwargs)

    def update_data(self, snap) -> None:
        services = snap.services
        net = snap.network

        fw_color = COL_LABEL if "Aktif" in services.firewall else "#ff5555"
        adg_color = COL_LABEL if "Aktif" in services.adguard else "#888888"

        lines = [
            f"[{COL_LABEL}]{'Firewall   :':<16}[/][bold {fw_color}]{services.firewall}[/]",
            f"[{COL_LABEL}]{'Conntrack  :':<16}[/][bold {COL_VALUE}]{net.conntrack:,}[/] / [dim]{net.conntrack_max:,}[/]",
            f"[{COL_LABEL}]{'DNS sorgu  :':<16}[/][bold {COL_VALUE}]{services.dns_queries:,}[/]",
            f"[{COL_LABEL}]{'AdGuardHome:':<16}[/][bold {adg_color}]{services.adguard}[/]",
        ]
        self.update("\n".join(lines))
