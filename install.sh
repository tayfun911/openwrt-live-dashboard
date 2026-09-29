#!/bin/sh
# ============================================================
# OpenWrt Live Dashboard — Kurulum Betiği
#
# Kullanım:
#   sh install.sh          # kiosk modu (HDMI otomatik başlatma, önerilir)
#   KIOSK=0 sh install.sh  # sadece procd servisi olarak
#   sh install.sh --uninstall
# ============================================================

set -e

DASH_DIR="/root/openwrt-dashboard"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> OpenWrt Live Dashboard kurulumu başlıyor..."

# ---- Kaldırma ----
if [ "$1" = "--uninstall" ]; then
    echo "==> Kaldırılıyor..."
    /etc/init.d/openwrt-dashboard stop 2>/dev/null || true
    /etc/init.d/openwrt-dashboard disable 2>/dev/null || true
    rm -f /etc/init.d/openwrt-dashboard
    if [ -f /etc/inittab.bak ]; then
        cp /etc/inittab.bak /etc/inittab
        echo "==> inittab geri yüklendi."
    fi
    rm -rf "$DASH_DIR"
    echo "==> Kaldırma tamam."
    exit 0
fi

KIOSK="${KIOSK:-1}"

# ---- 1) Bağımlılıklar ----
# OpenWrt 25.x+ "apk" paket yöneticisini kullanır; eski sürümlerde opkg
if command -v apk >/dev/null 2>&1; then
    echo "==> apk ile Python bağımlılıkları kuruluyor..."
    apk update || true
    apk add python3 || true
    if ! command -v pip3 >/dev/null 2>&1; then
        for PKG in python3-pip py3-pip; do
            apk add "$PKG" && break
        done
    fi
elif command -v opkg >/dev/null 2>&1; then
    echo "==> opkg ile Python bağımlılıkları kuruluyor..."
    opkg update || true
    opkg install python3 python3-pip || true
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "!! python3 bulunamadı."
    echo "   Kurun: apk add python3 py3-pip   (veya sh service/bootstrap_python.sh)"
    exit 1
fi

echo "==> textual kuruluyor (pip)..."
if ! pip3 install --upgrade textual rich; then
    python3 -m pip install --upgrade textual rich || {
        echo "!! textual kurulamadı."; exit 1;
    }
fi

# ---- 2) Dosyaları kopyala ----
echo "==> Dosyalar $DASH_DIR içine kopyalanıyor..."
mkdir -p "$DASH_DIR"
cp -r "$PROJECT_DIR"/. "$DASH_DIR"/

# ---- 3) procd servisi ----
echo "==> procd servisi kuruluyor..."
cp "$DASH_DIR/service/openwrt-dashboard.init" /etc/init.d/openwrt-dashboard
chmod +x /etc/init.d/openwrt-dashboard
/etc/init.d/openwrt-dashboard enable

if [ "$KIOSK" = "1" ]; then
    echo "==> Kiosk modu: HDMI konsol otomatik başlatma ayarlanıyor..."
    cp /etc/inittab /etc/inittab.bak

    # busybox init uyumlu satır (tty1 respawn + sarmalayıcı betik) kurar
    sh "$DASH_DIR/service/fix_kiosk.sh" || true

    # procd servisini kiosk ile çift çalıştırmamak için kapat
    /etc/init.d/openwrt-dashboard disable || true
    echo "==> Yeniden başlatıldığında dashboard HDMI'da otomatik açılacak."
    echo "==> (Geri almak için: sh install.sh --uninstall)"
else
    echo "==> procd servisi başlatılıyor..."
    /etc/init.d/openwrt-dashboard start
fi

echo "==> Tamam. Manuel test: cd $DASH_DIR && python3 dashboard.py"
echo "==> 256 renk için fbterm önerilir: opkg install fbterm"
