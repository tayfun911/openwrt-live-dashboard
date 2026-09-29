"""Ağ/WAN paneli: WAN IP, internet, ping, toplam trafik, arayüzler."""
from __future__ import annotations

from .base import Panel, fmt_speed, fmt_bytes, COL_LABEL, COL_VALUE


class NetworkPanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__("Ag / WAN", **kwargs)

    def update_data(self, snap) -> None:
        net = snap.network
        lines: list[str] = []

        # ---- WAN özeti (kompakt) ----
        lines.append(f"[{COL_LABEL}]{'WAN IPv4 :':<10}[/][bold {COL_VALUE}]{net.wan_ipv4 or '-'}[/]")
        lines.append(f"[{COL_LABEL}]{'WAN IPv6 :':<10}[/][bold {COL_VALUE}]{net.wan_ipv6 or '-'}[/]")
        if net.wan_proto or net.wan_address:
            lines.append(
                f"[{COL_LABEL}]{'Proto    :':<10}[/][bold {COL_VALUE}]{net.wan_proto.upper()}[/]"
                f"  [bold {COL_VALUE}]{net.wan_address}[/]"
            )
        if net.wan_gateway:
            lines.append(f"[{COL_LABEL}]{'Gateway  :':<10}[/][bold {COL_VALUE}]{net.wan_gateway}[/]")
        if net.wan_dns:
            lines.append(
                f"[{COL_LABEL}]{'DNS      :':<10}[/][bold {COL_VALUE}]{', '.join(net.wan_dns)}[/]"
            )

        internet = (
            f"[bold {COL_LABEL}]OK[/] [dim]{net.internet_latency_ms:.0f}ms[/]"
            if net.internet
            else "[bold #ff5555]X[/]"
        )
        pings = "  ".join(
            f"[{COL_LABEL}]{p.host}[/][bold {COL_LABEL if p.alive else '#ff5555'}]:"
            f"{p.latency_ms:.0f}ms[/]"
            for p in net.pings
        )
        lines.append(f"[{COL_LABEL}]{'Internet :':<10}[/]{internet}  {pings}")

        lines.append(
            f"[{COL_LABEL}]D:[/][bold {COL_VALUE}]{fmt_speed(net.total_rx_rate)}[/]  "
            f"[{COL_LABEL}]U:[/][bold {COL_VALUE}]{fmt_speed(net.total_tx_rate)}[/]  "
            f"[dim]({fmt_bytes(net.total_rx)} / {fmt_bytes(net.total_tx)})[/]"
        )

        # ---- Arayüzler (kompakt: satır başına 2, en fazla 4) ----
        ifaces = [i for i in net.interfaces if i.name != "lo"][:4]
        if ifaces:
            lines.append("[#45606e]--- Arayuzler ---[/]")
            cells = []
            for iface in ifaces:
                if iface.up and iface.name.startswith("wlan"):
                    cells.append(f"{iface.name} UP {net.wifi_clients}ist")
                else:
                    cells.append(f"{iface.name} {'UP' if iface.up else 'DN'}")
            for i in range(0, len(cells), 2):
                pair = cells[i : i + 2]
                lines.append(f"[{COL_LABEL}]" + "   ".join(pair) + "[/]")

        if net.wifi_ssid:
            lines.append(f"[{COL_LABEL}]{'SSID     :':<10}[/][bold {COL_VALUE}]{net.wifi_ssid}[/]")

        self.update("\n".join(lines))
