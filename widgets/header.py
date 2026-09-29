"""Üst bilgi paneli: OpenWrt logosu, durum göstergeleri, saat."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from .base import Panel, fmt_speed, fmt_bytes, fmt_uptime

LOGO = """[bold #FFD700]█████ █████ █████ █████ █    
█     █   █ █   █   █   █    
█     █   █ █████   █   █    
█████ █████ █     █████ █████[/]"""


class HeaderPanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__(title="", subtitle="", id="header", **kwargs)
        # Panel'in programatik çerçevesini kaldır: header'da SADECE alt çizgi
        # olsun (üst çerçeve satır yiyip logoyu kırpıyordu).
        self.styles.border = ("none", "#B26CFF")
        self.styles.border_bottom = ("solid", "#B26CFF")

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static(LOGO, markup=True, classes="logo")
            self._status = Static("", markup=True, classes="header-status")
            yield self._status

    def update_data(self, snap) -> None:
        net = snap.network
        cpu_pct = snap.cpu.total
        ram_pct = snap.memory.pct
        disk_pct = snap.disk.root_pct
        up = "[bold #00FF66]OK[/]" if net.internet else "[bold #ff5555]X[/]"

        status = [
            f"[bold #FFD700]{snap.hostname or 'OpenWrt'}[/]  "
            f"[#FFD700]OpenWrt[/] [bold #FFD700]{snap.openwrt_version or '?'}[/]",
            f"[bold #FFD700]{snap.datetime_str}[/]  "
            f"[#FFD700]Uptime[/] [bold #FFD700]{fmt_uptime(snap.uptime_s)}[/]",
            f"[#FFD700]CPU[/] [bold #FFD700]{cpu_pct:4.1f}%[/]  "
            f"[#FFD700]RAM[/] [bold #FFD700]{ram_pct:4.1f}%[/]  "
            f"[#FFD700]Disk[/] [bold #FFD700]{disk_pct:4.1f}%[/]  "
            f"[#FFD700]WAN[/] [bold #FFD700]{net.wan_ipv4 or '-'}[/] {up}",
            f"[#FFD700]D[/] [bold #FFD700]{fmt_speed(net.total_rx_rate)}[/]  "
            f"[#FFD700]U[/] [bold #FFD700]{fmt_speed(net.total_tx_rate)}[/]  "
            f"[#FFD700]WiFi[/] [bold #FFD700]{net.wifi_clients}[/]  "
            f"[#FFD700]CT[/] [bold #FFD700]{net.conntrack:,}[/]",
        ]
        self._status.update("\n".join(status))
