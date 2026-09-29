"""Neon mavi/yeşil cyber tema tanımı."""
from __future__ import annotations

from textual.theme import Theme

CYBER_THEME = Theme(
    name="cyber",
    primary="#FFD700",       # sarı (vurgu / accent)
    secondary="#B26CFF",     # mor (çerçeveler)
    accent="#FFD700",
    foreground="#6FB7FF",    # mavi (yazılar / değerler)
    background="#001018",    # neredeyse siyah mavi
    success="#A8E6A3",       # fıstık yeşili
    warning="#ffd166",
    error="#ff5555",
    surface="#01141c",
    panel="#021a22",
    dark=True,
    variables={
        "block-cursor-text": "#001018",
        "block-cursor-background": "#FFD700",
        "footer-background": "#01141c",
        "footer-foreground": "#FFD700",
        "input-background": "#01141c",
        "input-foreground": "#6FB7FF",
        "input-border": "#B26CFF",
        "button-default-background": "#2a1038",
        "button-default-foreground": "#FFD700",
        "button-focus-background": "#FFD700",
        "button-focus-foreground": "#001018",
    },
)
