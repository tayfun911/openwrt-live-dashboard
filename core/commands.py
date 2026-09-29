"""Düşük seviye yardımcılar: komut çalıştırma ve /proc, /sys okuma.

Tüm fonksiyonlar "asla hata fırlatmaz" prensibiyle yazılmıştır; bir kaynak
yoksa veya Linux dışı bir sistemde çalışılıyorsa boş/varsayılan değer döner.
Böylece aynı kod Windows'ta da (geliştirme önizlemesi olarak) çalışır.
"""
from __future__ import annotations

import os
import re
import subprocess

IS_LINUX = os.name == "posix"
PROC = "/proc" if IS_LINUX else None

_TIMEOUT = 2.0  # saniye


def run(cmd: str, timeout: float = _TIMEOUT) -> str:
    """Bir kabuk komutunu çalıştırır, stdout döndürür (hata olursa '')."""
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="replace",
        )
        return proc.stdout or ""
    except Exception:
        return ""


def run_list(cmd: str, timeout: float = _TIMEOUT) -> list[str]:
    """Komut çıktısını boş satırlar elenmiş liste olarak döndürür."""
    return [ln for ln in run(cmd, timeout).splitlines() if ln.strip()]


def read_proc(path: str) -> str:
    """Bir /proc dosyasını okur (Linux değilse '' döner)."""
    if not IS_LINUX:
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return ""


def read_sys(path: str) -> str:
    """Bir /sys dosyasını okur ve satır sonunu temizler."""
    if not IS_LINUX:
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().strip()
    except Exception:
        return ""


def read_int(path: str, default: int = 0) -> int:
    """Bir /sys dosyasından tamsayı okur."""
    text = read_sys(path)
    try:
        return int(text)
    except ValueError:
        return default


def parse_int(text: str, default: int = 0) -> int:
    """Metin içindeki ilk tamsayıyı döndürür."""
    match = re.search(r"-?\d+", text)
    return int(match.group()) if match else default


def first_line(text: str) -> str:
    """İlk satırı temizlenmiş olarak döndürür."""
    stripped = text.strip()
    return stripped.splitlines()[0].strip() if stripped else ""
