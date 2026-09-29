# OpenWrt Live Dashboard (Türkçe)

> 🇬🇧 **English documentation: [README.md](README.md)**

OpenWrt çalıştıran bir **LattePanda** üzerinde, HDMI'a bağlı monitörde siyah
konsol ekranı yerine gösterilen **tam ekran canlı durum ekranı**. Python +
[Textual](https://textual.textualize.io/) ile yazılmıştır; konsol uyumlu
renkli kutular (mor çerçeve, yeşil etiket, mavi değer, sarı üst bilgi) ve
canlı bant grafikleri içerir.

> Router açılır açılmaz HDMI'da otomatik açılır ve profesyonel ağ
> cihazlarındaki gibi canlı istatistik gösterir.

---

## 🖥️ Özellikler

| Kategori | Gösterilenler |
|---|---|
| ⚡ **CPU** | Toplam + çekirdek bazında kullanım, frekans, sıcaklık, load |
| 🧠 **Bellek** | RAM kullanımı, cache, buffer, kullanılabilir |
| 💾 **Disk** | Root doluluk, eMMC sıcaklığı (varsa) |
| 🌐 **Ağ/WAN** | WAN IPv4/IPv6, internet testi, ping (1.1.1.1 / 8.8.8.8) + paket kaybı |
| 📊 **Trafik** | Anlık indirme/yükleme hızı, toplam trafik, canlı bant grafiği |
| 🖧 **Arayüzler** | eth0/eth1/wlan durumları, link hızı (100M / 1G / 2.5G) |
| 📶 **Wi-Fi** | İstemci sayısı, SSID |
| 👥 **LAN** | Bağlı cihazlar: IP + MAC + Hostname + cihaz başına anlık trafik |
| 🔥 **Conntrack** | Aktif bağlantı sayısı / maksimum |
| 🧱 **Firewall** | nftables/iptables durumu |
| 🔐 **VPN** | WireGuard (peer sayısı), OpenVPN |
| 🚀 **Proxy** | Passwall, Xray, sing-box |
| 🐳 **Docker** | Konteyner listesi + CPU/RAM |
| 🛡 **DNS** | DNS sorgu sayısı, AdGuard Home durumu |
| 📜 **Loglar** | Son 20 satır, **hatalar kırmızı** |
| ⚙️ **Sistem** | Uptime, tarih/saat, kernel & OpenWrt sürümü, hostname |

**Kısayollar:** `F1` yardım · `F5` anında yenile · `Q` çıkış · `Esc` kapat
**Güncelleme:** 1 saniye (`config.json` ile değiştirilebilir)

---

## 📁 Proje Yapısı

```
openwrt-dashboard/
├── dashboard.py            # Ana uygulama (Textual App)
├── config.json             # Yapılandırma
├── requirements.txt
├── install.sh              # OpenWrt kurulum betiği
├── core/
│   ├── config.py           # Yapılandırma yükleme
│   ├── commands.py         # Komut / /proc / /sys yardımcıları
│   ├── models.py           # Veri modelleri (dataclass)
│   └── collector.py        # Veri toplama katmanı
├── widgets/
│   ├── base.py             # Panel tabanı + biçimlendirme yardımcıları
│   ├── header.py           # OpenWrt logosu + durum göstergeleri
│   ├── cpu.py / memory.py / disk.py / temperature.py
│   ├── network.py / clients.py
│   ├── firewall.py / vpn.py / docker.py
│   ├── logs.py / graph.py / help.py
├── themes/
│   ├── cyber.py            # Neon mavi/yeşil tema
│   └── cyber.tcss          # Düzen (CSS)
├── service/
│   ├── openwrt-dashboard.init   # procd servisi
│   ├── run-dashboard.sh         # tty1 sarmalayıcı (TERM + dmesg -n 1)
│   ├── fix_kiosk.sh             # inittab'ı busybox uyumlu hale getirir
│   └── bootstrap_python.sh      # apk/opkg yoksa bağımsız Python kurar
└── tests/
    └── smoke_test.py       # Hızlı doğrulama
```

---

## 🚀 Kurulum (LattePanda / OpenWrt) — Gerçek Adım Adım

Bu bölüm, projeyi **gerçek bir OpenWrt 25.12.5 (x86/64, minimal imaj)**
üzerine kurarken izlenen ve doğrulanan adımların tamamıdır. Windows
bilgisayardan SSH ile çalışılır.

### 0) Ön koşullar / Durum Tespiti

```sh
cat /etc/openwrt_release          # OpenWrt sürümü
command -v apk opkg python3 pip3  # hangileri var?
```

- **OpenWrt 25.x+ artık `opkg` yerine `apk` kullanır.** `opkg` yoksa şaşırmayın.
- Minimal imajlarda `python3` hiç olmayabilir. `install.sh` `apk`/`opkg`'yi
  otomatik tanır; ikisi de yoksa `service/bootstrap_python.sh` ile bağımsız
  Python kurulur.

### 1) Projeyi sıkıştırın (Windows'ta)

```powershell
# gereksiz dosyaları hariç tutarak arşivle
tar -czf openwrt-dashboard.tar.gz --exclude=".venv" --exclude="__pycache__" --exclude="*.pyc" -C <proje-klasoru> .
```

> ⚠️ **CRLF uyarısı:** Windows'ta oluşturulan dosyalar CRLF (`\r\n`) satır
> sonu içerir; bu, init betiğinin `#!/bin/sh /etc/rc.common` shebang'ını
> bozar (`.common` hatası). Deploy öncesi tüm dosyaları LF'ye çevirin:
> ```powershell
> python -c "import pathlib; p=pathlib.Path(r'.'); [f.write_bytes(f.read_bytes().replace(b'\r\n', b'\n')) for f in p.rglob('*') if f.is_file() and f.suffix in {'.py','.sh','.init','.tcss','.md','.json'} and '.venv' not in str(f) and '__pycache__' not in str(f)]"
> ```

### 2) Router'a gönderin (Windows PowerShell)

> ⚠️ **`scp -O` şart!** Router'ın SSH'ında (dropbear) `sftp-server` yok;
> OpenSSH `scp` varsayılan olarak SFTP kullanır ve `sftp-server: not found`
> hatası verir. Eski SCP protokolü için **`-O`** bayrağını kullanın:

```powershell
scp -O openwrt-dashboard.tar.gz root@192.168.1.1:/tmp/
```

İlk bağlantıda host anahtarı değişmişse (yeniden flash sonrası):
```powershell
ssh-keygen -R 192.168.1.1   # eski anahtarı temizle, tekrar dene
```

### 3) Kurun (SSH)

```sh
ssh root@192.168.1.1
cd /tmp && rm -rf owd && mkdir owd && tar xzf openwrt-dashboard.tar.gz -C owd && cd owd && sh install.sh
```

`install.sh` sırasıyla:

1. `apk` (varsa) ile `python3` + `python3-pip` kurar
   *(paket adı `py3-pip` değil, **`python3-pip`**!)*
2. `pip3 install textual rich` (birkaç dakika sürebilir)
3. Dosyaları `/root/openwrt-dashboard` içine kopyalar
4. procd servisini kurar (`/etc/init.d/openwrt-dashboard`)
5. **Kiosk modu** (varsayılan): `/etc/inittab`'ı yedekler, konsol login
   satırını kapatır ve dashboard'u `tty1` (HDMI) üzerinde `respawn` eder

**Bağımsız Python gerekirse** (apk/opkg hiç yoksa):
```sh
sh service/bootstrap_python.sh   # /opt/python + pip + textual
sh install.sh
```

### 4) Doğrulayın

```sh
cd /root/openwrt-dashboard && python3 -m py_compile dashboard.py core/*.py widgets/*.py && echo OK
ps w | grep dashboard          # dashboard.py süreci görünmeli
grep -n dashboard /etc/inittab # tty1 respawn satırı görünmeli
```

### 5) Yeniden başlatın

Kiosk'un devreye girmesi için router'ı yeniden başlatın (`reboot`). Açılışta
dashboard HDMI'da otomatik başlar.

**Yeniden başlatmadan hemen test / yeniden yükleme:**

```sh
init q             # inittab'ı yeniden oku (yeniden başlatmadan)
killall python3    # dashboard'u yeniden başlat (respawn yakalar)
```

Geri almak için:

```sh
sh install.sh --uninstall
```

---

## ⚙️ Yapılandırma

`config.json`:

```json
{
  "refresh_interval": 1.0,        // saniye cinsinden güncelleme
  "graph_points": 90,             // grafikteki nokta sayısı
  "log_lines": 20,                // gösterilecek log satırı
  "wan_interface": "wan",         // WAN arayüz adı
  "wifi_interfaces": ["wlan0", "wlan1"],
  "ping_hosts": ["1.1.1.1", "8.8.8.8"],
  "show_emmc": true               // eMMC sıcaklığı ara
}
```

---

## 🎨 Renk ve Konsol Notları

**Renk düzeni** (konsol uyumlu):

| Öğe | Renk |
|---|---|
| Etiketler (Toplam, Kullanim, WAN...) | Yeşil `#00FF66` |
| Değerler / yazılar | Mavi `#6FB7FF` |
| Çerçeveler / panel başlıkları | Mor `#B26CFF` |
| COPIL logo + üst bilgi | Sarı `#FFD700` |

Renkler `widgets/base.py` (COL_* sabitleri) ve `themes/cyber.py` içinde.

**Konsol fontu sınırlamaları** (bu cihazın minimal imajında):
- Türkçe karakterler (ş ğ İ ı) konsol fontunda yok → arayüz tamamen ASCII.
- Çift çizgili kutu (╗╔╚╝═║) ve yuvarlak köşe (╭╮╰╯) yok → `border: solid`
  (tek çizgili) kullanılır; logo `█` blok karakterleriyle çizilir.
- Emoji yok → panel başlıklarında emoji kullanılmaz; ↓/↑ okları `D:`/`U:`.
- Pastel renkler 16 renkli konsolda beyaz görünür → doygun renkler kullanılır.
- `kbd`/`setfont`/`fbterm`/`terminus` bu imajın paket deposunda yok; bu
  yüzden konsol fontu değiştirilemez (Türkçe/yazı boyutu sınırlı kalır).
  Tam görünüm için standart (dolu) OpenWrt imajına geçilip `setfont` ile
  Terminus fontu kurulabilir.

**Çekirdek logları:** Dashboard üstüne kernel mesajları yazmasın diye
`service/run-dashboard.sh` içinde `dmesg -n 1` çalıştırılır.

- İlk CPU değeri bir çevrim sonrasında gerçek oranı gösterir (fark tabanlı).

## � Sorun Giderme

| Belirti | Çözüm |
|---|---|
| `sftp-server: not found` | `scp -O` kullanın (router'da SFTP yok) |
| `.common` hatası / shebang bozuk | Dosyalar CRLF — deploy öncesi LF'ye çevirin |
| Dashboard hiç başlamıyor | inittab satırı `tty1::respawn:/bin/sh /root/openwrt-dashboard/run-dashboard.sh` olmalı (busybox init kabuk sözdizimini işlemez); `init q` ile yeniden yükle |
| Loglar dashboard üstüne düşüyor | `dmesg -n 1` (run-dashboard.sh içinde zaten var) |
| Etiketler beyaz görünüyor | Konsol 16 renk; pastel yerine doygun yeşil `#00FF66` kullanın |
| `py3-pip (no such package)` | Paket adı `python3-pip` |
| Dashboard'u elle yeniden başlatma | `killall python3` (busybox `pkill -f` güvenilmez) |
| SSH komutunda `python3 -c "..."` bozuluyor | PowerShell çift tırnakları bozar — ssh komutlarında çift tırnak kullanmayın |
| Türkçe karakterler bozuk / kayık logo | Konsol fontu sınırlı — tasarım buna göre (ASCII + blok logo + solid kenarlık) |

## �🧪 Geliştirici Doğrulaması

Windows/masaüstünde de düzen önizlenebilir (veriler "—" görünür):

```sh
pip install -r requirements.txt
python dashboard.py
python tests/smoke_test.py   # Textual test modunda hızlı doğrulama
```

---

## 🛠️ Veri Kaynakları

| Veri | Kaynak |
|---|---|
| CPU / RAM / uptime / load | `/proc/stat`, `/proc/meminfo`, `/proc/uptime`, `/proc/loadavg` |
| Arayüz trafiği | `/proc/net/dev` |
| Link hızı | `/sys/class/net/*/speed` + `iwinfo` |
| WAN IP | `ubus call network.interface.wan status` + `ip` |
| İstemci/SSID | `iwinfo <if> assoclist / info` |
| LAN cihazları | `/proc/net/arp` + `/tmp/dhcp.leases` |
| Cihaz trafiği | `/proc/net/nf_conntrack` (IP bazında) |
| Conntrack / DNS | `/proc/net/nf_conntrack` |
| VPN / proxy | `wg show`, `pgrep` |
| Docker | `docker ps` + `docker stats` |
| Loglar | `logread` |
