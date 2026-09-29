#!/bin/sh
# ============================================================
# Bağımsız Python kurulumu (python-build-standalone, musl)
#
# OpenWrt imajında opkg/python3 YOKSA (minimal/özel imaj) bu betik,
# pip dahil kendi başına çalışan bir Python'u /opt/python altına
# kurar ve /usr/bin/python3, pip3 vb. için symlink oluşturur.
#
# Kullanım:
#   sh service/bootstrap_python.sh
# ============================================================
set -e

ARCH="x86_64-unknown-linux-musl"
PREFIX="/opt/python"
TMP="/tmp/pybuild"

echo "==> Bağımsız Python indiriliyor (python-build-standalone)..."
mkdir -p "$TMP" "$PREFIX"
cd "$TMP"

# GitHub API: en son sürümün musl install_only arşivini bul
echo "==> GitHub'da en son sürüm aranıyor..."
ASSET_URL=$(curl -fsSL --retry 3 \
    https://api.github.com/repos/astral-sh/python-build-standalone/releases/latest \
    | grep -o 'https://[^"]*'"$ARCH"'-install_only\.tar\.gz' \
    | head -1)

if [ -z "$ASSET_URL" ]; then
    echo "!! GitHub'dan uygun sürüm bulunamadı." >&2
    exit 1
fi
echo "   Arşiv: $ASSET_URL"

curl -fL --retry 3 -o python.tar.gz "$ASSET_URL"

echo "==> /opt/python içine açılıyor..."
rm -rf "$PREFIX"
mkdir -p "$PREFIX"
tar xzf python.tar.gz -C "$PREFIX"
if [ -d "$PREFIX/python" ]; then
    (cd "$PREFIX" && mv python/* . && rmdir python)
fi

# Küresel erişim: ssh/init oturumlarında da python3/pip3 çalışsın
echo "==> Symlink'ler oluşturuluyor..."
for BIN in python3 python pip3 pip; do
    if [ -e "$PREFIX/bin/$BIN" ]; then
        ln -sf "$PREFIX/bin/$BIN" "/usr/bin/$BIN"
    fi
done

echo "==> Versiyon:"
python3 --version

echo "==> pip güncelleniyor..."
python3 -m pip install --no-cache-dir --upgrade pip

echo "==> textual + rich kuruluyor..."
python3 -m pip install --no-cache-dir textual rich

echo "==> Doğrulama:"
python3 -c "import textual; print('textual', textual.__version__)"
echo "==> Python kurulumu TAMAM"
