#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenWrt Live Dashboard — ana uygulama.

OpenWrt çalıştıran bir LattePanda'nın HDMI'ına bağlı monitörde, kara
konsol ekranı yerine tam ekran canlı durum ekranı gösterir.

Çalıştırma:
    python3 dashboard.py

Kısayollar: F1 yardım · F5 yenile · Q çıkış
"""
from __future__ import annotations

import os

# Kernel konsolu (fbcon) yalnızca 16 renk gösterir; truecolor/256 renk
# gönderimi yanlış renkler (mor görünen pembe vb.) üretir. TERM'i 'linux'
# yaparak Textual/Rich'in doğrudan 16 renkli ANSI kodu göndermesini
# sağlıyoruz (procd/inittab nasıl başlatırsa başlatsın zorla uygulanır).
os.environ["TERM"] = "linux"
os.environ.pop("COLORTERM", None)

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll

from core.collector import Collector
from core.config import Config
from themes.cyber import CYBER_THEME

from widgets.base import Panel
from widgets.header import HeaderPanel
from widgets.cpu import CpuPanel
from widgets.memory import MemoryPanel
from widgets.disk import DiskPanel
from widgets.temperature import TemperaturePanel
from widgets.network import NetworkPanel
from widgets.clients import ClientsPanel
from widgets.firewall import FirewallPanel
from widgets.logs import LogsPanel
from widgets.graph import GraphPanel
from widgets.help import HelpScreen

BASE_DIR = Path(__file__).resolve().parent


class OpenWrtDashboard(App):
    """OpenWrt canlı durum ekranı."""

    TITLE = "OpenWrt Live Dashboard"
    SUB_TITLE = "OpenWrt / LattePanda canli durum ekrani"
    CSS_PATH = str(BASE_DIR / "themes" / "cyber.tcss")
    # Footer'daki "palette" (komut paleti) bağlantısını kapat
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("f1", "show_help", "Yardim", show=True),
        Binding("f5", "refresh", "Yenile", show=True),
        Binding("q", "quit", "Cikis", show=True),
    ]

    def __init__(self, config: Config | None = None) -> None:
        super().__init__()
        self.config = config or Config.load(BASE_DIR / "config.json")
        self.collector = Collector(self.config)

    def compose(self) -> ComposeResult:
        yield HeaderPanel()

        with Horizontal(id="main-row"):
            with VerticalScroll(id="left-col"):
                yield NetworkPanel(id="network-panel")
                yield ClientsPanel(id="clients-panel")
                yield LogsPanel(id="logs-panel")

            with VerticalScroll(id="right-col"):
                yield CpuPanel(id="cpu-panel")
                yield MemoryPanel(id="memory-panel")
                yield DiskPanel(id="disk-panel")
                yield TemperaturePanel(id="temperature-panel")
                yield FirewallPanel(id="firewall-panel")
                yield GraphPanel(id="graph-panel")

    def on_mount(self) -> None:
        self.register_theme(CYBER_THEME)
        self.theme = "cyber"
        self.set_interval(self.config.refresh_interval, self.tick)
        self.tick()
        # Açılış sırasında konsola düşen boot mesajlarını tam ekran
        # yenilemeyle sil (ilk ~14 saniye boyunca 2 sn'de bir).
        self.set_interval(2.0, self._boot_clear, repeat=7)

    def _boot_clear(self) -> None:
        """Önyükleme artığı konsol yazılarını tam ekran yenilemeyle temizler."""
        self.screen.refresh()

    def tick(self) -> None:
        """Her çevrimde: veriyi topla ve tüm panellere dağıt."""
        snapshot = self.collector.collect()
        for widget in self.query(Panel):
            widget.update_data(snapshot)

    def action_refresh(self) -> None:
        """F5 — anında yenile."""
        self.tick()

    def action_show_help(self) -> None:
        """F1 — yardım ekranı."""
        self.push_screen(HelpScreen())


if __name__ == "__main__":
    OpenWrtDashboard().run()
