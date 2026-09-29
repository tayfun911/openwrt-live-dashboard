#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Konsol renk paletini ayarlar.

Kernel konsolu (fbcon) yalnizca 16 renk gosterir ve TEXTUAL bu paletin
13. slotuna (parlak magenta) #FF00FF / #B26CFF gibi renkleri esler.
Varsayilan slot 13 = (255,85,255) morumsu-pembe oldugundan kullanici
"mor" gorur. Bu script slot 13'u gercek neon pembeye (255,46,196) ceker.
"""
import fcntl
import os

PIO_CMAP = 0x4B71  # Konsol paletini yaz
GIO_CMAP = 0x4B70  # Konsol paletini oku (dogrulama icin)

# Varsayilan VGA/fbcon 16 renk paleti
DEFAULTS = [
    (0, 0, 0), (170, 0, 0), (0, 170, 0), (170, 85, 0),
    (0, 0, 170), (170, 0, 170), (0, 170, 170), (170, 170, 170),
    (85, 85, 85), (255, 85, 85), (85, 255, 85), (255, 255, 85),
    (85, 85, 255), (255, 85, 255), (85, 255, 255), (255, 255, 255),
]

# Slot 13 -> canli neon pembe (#FF2EC4)
NEON_PINK = (255, 46, 196)


def set_palette(dev: str = "/dev/tty1") -> bool:
    pal = bytearray(48)
    for i, (r, g, b) in enumerate(DEFAULTS):
        pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2] = r, g, b
    pal[13 * 3], pal[13 * 3 + 1], pal[13 * 3 + 2] = NEON_PINK
    try:
        fd = os.open(dev, os.O_RDWR)
        try:
            fcntl.ioctl(fd, PIO_CMAP, pal)
        finally:
            os.close(fd)
        # Dogrula
        check = bytearray(48)
        fd = os.open(dev, os.O_RDWR)
        try:
            fcntl.ioctl(fd, GIO_CMAP, check)
        finally:
            os.close(fd)
        got = (check[13 * 3], check[13 * 3 + 1], check[13 * 3 + 2])
        print(f"palette set OK on {dev}: slot13={got}")
        return got == NEON_PINK
    except Exception as e:  # noqa: BLE001
        print(f"palette err on {dev}: {e}")
        return False


if __name__ == "__main__":
    for dev in ("/dev/tty1", "/dev/console", "/dev/tty0"):
        if set_palette(dev):
            break
