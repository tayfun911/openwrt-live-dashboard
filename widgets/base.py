"""Ortak panel tabanı ve biçimlendirme yardımcıları."""
from __future__ import annotations

from textual.widgets import Static


class Panel(Static):
    """Kenarlıklı, başlıklı ve canlı içerikli temel panel."""

    def __init__(self, title: str = "", subtitle: str = "", **kwargs) -> None:
        super().__init__(markup=True, classes="panel", **kwargs)
        self.border_title = title
        self.border_subtitle = subtitle
        # Neon pembe çerçeve + başlık (CSS öncelik/önbellek sorunlarını bypass eder)
        self.styles.border = ("solid", "#FF00FF")
        self.styles.border_title_color = "#FF00FF"

    def update_data(self, snapshot) -> None:
        """Alt sınıflar bu yöntemi doldurur (anlık görüntüyü işler)."""
        raise NotImplementedError


# ----------------------------------------------------------------------
#  Konsol uyumlu renk paleti
# ----------------------------------------------------------------------
COL_LABEL = "#00FF66"   # yeşil — statik etiketler (konsol için doygun)
COL_VALUE = "#6FB7FF"   # mavi — değerler / yazılar
COL_YELLOW = "#FFD700"  # sarı — logo + üst bilgi
COL_PURPLE = "#B26CFF"  # mor — çerçeveler


# ----------------------------------------------------------------------
#  Biçimlendirme yardımcıları
# ----------------------------------------------------------------------
def heat_color(pct: float) -> str:
    """Yüke göre renk: yeşil -> sarı -> kırmızı."""
    if pct < 50:
        return "#00ff9c"
    if pct < 75:
        return "#ffd166"
    return "#ff5555"


def bar(pct: float, width: int = 22, color: str | None = None) -> str:
    """Unicode blok karakterli dikey ilerleme çubuğu (markup)."""
    pct = max(0.0, min(100.0, pct))
    color = color or heat_color(pct)
    filled = int(round(width * pct / 100.0))
    fill = "█" * filled
    empty = "░" * (width - filled)
    return f"[{color}]{fill}[/][#0a3a44]{empty}[/] {pct:5.1f}%"


def fmt_speed(bps: float) -> str:
    """Byte/sn değerini okunur hıza çevirir."""
    if bps >= 1_000_000_000:
        return f"{bps/1e9:.2f} Gbps"
    if bps >= 1_000_000:
        return f"{bps/1e6:.2f} Mbps"
    if bps >= 1_000:
        return f"{bps/1e3:.1f} kbps"
    return f"{bps:.0f} B/s"


def fmt_bytes(n: int) -> str:
    """Bayt değerini okunur boyuta çevirir."""
    if n >= 1 << 30:
        return f"{n/(1<<30):.2f} GiB"
    if n >= 1 << 20:
        return f"{n/(1<<20):.1f} MiB"
    if n >= 1 << 10:
        return f"{n/(1<<10):.0f} KiB"
    return f"{n} B"


def fmt_link(mbps) -> str:
    """Bağlantı hızını (Mbps) kısa gösterime çevirir: 100M / 1G / 2.5G."""
    if not mbps:
        return "-"
    if mbps >= 1000:
        return f"{mbps/1000:g}G"
    return f"{int(mbps)}M"


def fmt_uptime(sec: float) -> str:
    """Saniyeyi '3g 4s 12d 05sn' biçimine çevirir."""
    sec = int(sec)
    days, rem = divmod(sec, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}g")
    if hours or days:
        parts.append(f"{hours}s")
    if minutes or hours or days:
        parts.append(f"{minutes}d")
    parts.append(f"{seconds}sn")
    return " ".join(parts)


def fmt_temp(c: float | None) -> str:
    if c is None:
        return "-"
    return f"{c:.0f}°C"
