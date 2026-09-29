#!/bin/sh
# Dashboard sarmalayıcısı: TERM ayarlar, çekirdek loglarını susturur ve
# dashboard'u tty1 (HDMI) üzerinde çalıştırır.
# KONSOL: kernel fbcon yalnızca 16 renk gösterir. xterm-256color/truecolor
# göndermek konsolun yanlış renk göstermesine yol açar -> TERM=linux şart.
export TERM=linux
unset COLORTERM
# Önyükleme mesajlarının çoğu basılsın (ilk 2 sn), sonra ekranı temizleyip
# dashboard'u başlat ki logo üstünde açılış yazıları kalmasın.
sleep 2
# Çekirdek mesajlarının dashboard üzerine yazmasını engelle (loglar logo üstüne düşmesin)
dmesg -n 1 2>/dev/null
# Konsol paletini ayarla (slot 13 -> neon pembe); çıktıyı ekrana hiç yazma
/usr/bin/python3 /root/openwrt-dashboard/service/palette.py >/dev/null 2>&1
# Açılış mesajlarını sil: ekranı temizle ve imleci başa al
printf '\033[2J\033[H\033[?25l'
exec /usr/bin/python3 /root/openwrt-dashboard/dashboard.py
