"""F1 yardım ekranı (modal)."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

HELP_TEXT = """[bold #FFD700]OpenWrt Live Dashboard - Yardim[/]

[bold #6FB7FF]Tuslar[/]
  [bold]F1[/]  Yardim ekrani
  [bold]F5[/]  Aninda yenile
  [bold]Q[/]  Cikis
  [bold]Esc[/] Bu ekrani kapat

[bold #6FB7FF]Gosterge Panelleri[/]
  CPU        : cekirdek bazinda kullanim, frekans, sicaklik, load
  Bellek     : RAM / cache / buffer
  Disk       : root doluluk
  Sicaklik   : CPU + eMMC sensorleri
  Ag / WAN   : WAN IPv4/IPv6, internet, ping, arayuzler, link hizlari, trafik
  LAN        : bagli cihazlar (IP/MAC/Hostname) ve anlik trafik
  Guvenlik   : firewall, conntrack, DNS sorgu sayisi, AdGuard
  VPN/Proxy  : WireGuard / OpenVPN / Passwall / Xray / sing-box
  Docker     : konteynerler + CPU/RAM
  Loglar     : son satirlar, hatalar kirmizi
  Grafik     : son 90 saniyelik indirme/yukleme bandi

[dim]Veriler her saniye yenilenir. Ayar dosyasi: config.json[/]
"""


class HelpScreen(ModalScreen[None]):
    BINDINGS = [Binding("escape", "dismiss", "Kapat")]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Static(HELP_TEXT, markup=True)
            yield Button("Kapat", id="help-close", variant="primary")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "help-close":
            self.dismiss(None)
