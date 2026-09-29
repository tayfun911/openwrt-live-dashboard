"""Uygulama yapılandırması (config.json'dan okunur)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Dashboard yapılandırması.

    config.json içindeki anahtarlar bu alanlarla eşleşir.
    """

    refresh_interval: float = 1.0          # saniye cinsinden güncelleme aralığı
    graph_points: int = 90                 # trafik grafiğinde tutulacak nokta sayısı
    log_lines: int = 20                    # log panelinde gösterilecek satır sayısı
    wan_interface: str = "wan"             # WAN arayüz adı (ubus/ip için)
    wifi_interfaces: list[str] = field(default_factory=lambda: ["wlan0", "wlan1"])
    ping_hosts: list[str] = field(default_factory=lambda: ["1.1.1.1", "8.8.8.8"])
    show_emmc: bool = True                 # eMMC sıcaklığı ara (varsa)

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        """config.json dosyasını okur; eksik/hatalıysa varsayılanlarla döner."""
        cfg = cls()
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for key, value in data.items():
                if hasattr(cfg, key):
                    setattr(cfg, key, value)
        except Exception:
            # Dosya yok veya bozuk -> varsayılan yapılandırma kullanılır
            pass
        return cfg
