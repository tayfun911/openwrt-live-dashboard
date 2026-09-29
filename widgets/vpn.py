"""VPN / Proxy paneli: WireGuard, OpenVPN, Passwall, Xray, sing-box."""
from __future__ import annotations

from .base import Panel, COL_LABEL


class VpnPanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__("VPN / Proxy", **kwargs)

    def update_data(self, snap) -> None:
        services = snap.services

        def row(name: str, value: str) -> str:
            color = COL_LABEL if "Aktif" in value else "#888888"
            return f"[{COL_LABEL}]{name:<10}:[/] [bold {color}]{value}[/]"

        lines = [
            row("WireGuard", services.wireguard),
            row("OpenVPN", services.openvpn),
            row("Passwall", services.passwall),
            row("Xray", services.xray),
            row("sing-box", services.singbox),
        ]
        self.update("\n".join(lines))
