#!/bin/sh
# Kiosk düzeltmesi: dashboard'u tty1 (HDMI) konsoluna bağlar.
#
# Neden: busybox init, inittab'daki kabuk sözdizimini (/bin/sh -c '...'
# ve yönlendirmeler) işlemez; doğru yol, id alanına tty1 verilmiş sade bir
# respawn satırıdır. Bu betik eski bozuk satırı kaldırıp doğrusunu yazar.
set -e

DASH=/root/openwrt-dashboard
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Sarmalayıcı kopyalanıyor..."
cp "$SCRIPT_DIR/run-dashboard.sh" "$DASH/run-dashboard.sh"
chmod +x "$DASH/run-dashboard.sh"

echo "==> inittab güncelleniyor..."
# Eski '::respawn:' satırlarını kaldır (bozuk satır dahil)
grep -v '::respawn:' /etc/inittab > /tmp/inittab.new
# Doğru tty1 respawn satırını ekle
echo "tty1::respawn:/bin/sh $DASH/run-dashboard.sh" >> /tmp/inittab.new
cp /tmp/inittab.new /etc/inittab

echo "==> init yeniden yükleniyor..."
kill -HUP 1 2>/dev/null || true

sleep 2
echo "==> Sonuç:"
grep -n "respawn\|askfirst" /etc/inittab
echo "==> Dashboard süreci:"
ps w | grep -i dashboard | grep -v grep || echo "   (henüz başlamadı / başlatılıyor)"
echo "==> Kiosk düzeltildi."
