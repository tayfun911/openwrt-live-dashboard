"""Sistem verisi toplayıcısı (OpenWrt / Linux).

Tüm panellerin ihtiyacı olan veri, her çevrimde tek bir `collect()`
çağrısıyla alınır. Veriler /proc, /sys ve OpenWrt komutlarından
(ubus, iwinfo, wg, docker, logread ...) toplanır. Eksik ya da erişilemez
kaynaklar hata üretmez; boş / "—" değer olarak döner.

Ağır işlemler (ping, wifi, cihaz listesi, docker) kısa süreli önbellekte
tutulur ki 1 saniyelik güncelleme akıcı kalsın.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from collections import deque

from .commands import IS_LINUX, PROC, run, run_list, read_proc, read_sys, read_int, first_line
from .models import (
    SystemSnapshot,
    CpuInfo,
    MemoryInfo,
    DiskInfo,
    NetworkInfo,
    IfaceStat,
    PingResult,
    LanDevice,
    DockerContainer,
    ServiceInfo,
    LogEntry,
)


class Collector:
    """Veri toplama ve oran (rate) hesaplama."""

    def __init__(self, config) -> None:
        self.config = config
        self._prev_cpu: dict[str, tuple[int, int]] = {}
        self._prev_net: dict[str, tuple[int, int]] = {}
        self._prev_dev: dict[str, tuple[int, int]] = {}
        self._prev_dev_ts = 0.0
        self._last_net_ts = 0.0
        self.history_rx: deque[float] = deque(maxlen=config.graph_points)
        self.history_tx: deque[float] = deque(maxlen=config.graph_points)
        self._cache: dict[str, tuple[float, object]] = {}
        # IP -> hostname (ters DNS sonuçları; tekrar tekrar nslookup çalıştırmamak için)
        self._hostname_cache: dict[str, str] = {}
        # Ping sonuçları arka planda ölçülür (UI engellenmesin)
        self._ping_results: list[PingResult] = []
        self._ping_lock = threading.Lock()
        self._start_ping_thread()

    def _start_ping_thread(self) -> None:
        """Pinglemeyi arka planda çalıştırır; her çevrimde en güncel sonucu döndürür."""

        def worker() -> None:
            while True:
                try:
                    results = self._do_pings()
                except Exception:
                    results = []
                with self._ping_lock:
                    self._ping_results = results
                time.sleep(3)

        threading.Thread(target=worker, daemon=True, name="ping-worker").start()

    # ------------------------------------------------------------------
    #  Önbellek yardımcısı
    # ------------------------------------------------------------------
    def _cached(self, key: str, fn, ttl: float = 4.0):
        now = time.monotonic()
        hit = self._cache.get(key)
        if hit is not None and now - hit[0] < ttl:
            return hit[1]
        value = fn()
        self._cache[key] = (now, value)
        return value

    # ------------------------------------------------------------------
    #  ANA GİRİŞ
    # ------------------------------------------------------------------
    def collect(self) -> SystemSnapshot:
        snap = SystemSnapshot()
        snap.datetime_str = time.strftime("%Y-%m-%d %H:%M:%S")
        snap.uptime_s = self._uptime()
        snap.hostname = first_line(read_proc(f"{PROC}/sys/kernel/hostname")) or run("hostname").strip()
        snap.kernel = run("uname -r").strip()
        snap.openwrt_version = self._openwrt_version()
        snap.cpu = self._cpu()
        snap.memory = self._memory()
        snap.disk = self._disk()
        snap.network = self._network()
        snap.services = self._services()
        snap.logs = self._logs()
        snap.errors = sum(1 for e in snap.logs if e.is_error)
        return snap

    # ------------------------------------------------------------------
    #  SİSTEM GENEL
    # ------------------------------------------------------------------
    def _uptime(self) -> float:
        parts = read_proc(f"{PROC}/uptime").split()
        return float(parts[0]) if parts else 0.0

    def _openwrt_version(self) -> str:
        release = run("cat /etc/openwrt_release")
        m = re.search(r"DISTRIB_DESCRIPTION=['\"]?([^'\"]+)", release)
        if m:
            return m.group(1).strip()
        return run("cat /etc/openwrt_version").strip()

    # ------------------------------------------------------------------
    #  CPU
    # ------------------------------------------------------------------
    def _cpu(self) -> CpuInfo:
        info = CpuInfo()
        if PROC:
            text = read_proc(f"{PROC}/stat")
            lines = [ln for ln in text.splitlines() if ln.startswith("cpu")]
            if lines:
                total_line, *core_lines = lines
                for ln in core_lines:
                    toks = ln.split()
                    if len(toks) < 5:
                        continue
                    key = toks[0]
                    vals = [int(x) for x in toks[1:]]
                    total = sum(vals[:8])
                    idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
                    prev = self._prev_cpu.get(key)
                    if prev and total > prev[0]:
                        pct = 100.0 * (1.0 - (idle - prev[1]) / (total - prev[0]))
                        info.cores.append(max(0.0, min(100.0, pct)))
                    else:
                        info.cores.append(0.0)
                    self._prev_cpu[key] = (total, idle)

                toks = total_line.split()
                if len(toks) >= 5:
                    vals = [int(x) for x in toks[1:]]
                    total = sum(vals[:8])
                    idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
                    prev = self._prev_cpu.get("cpu")
                    if prev and total > prev[0]:
                        info.total = max(
                            0.0,
                            min(100.0, 100.0 * (1.0 - (idle - prev[1]) / (total - prev[0]))),
                        )
                    self._prev_cpu["cpu"] = (total, idle)

        # Frekans (MHz)
        for i in range(32):
            freq = read_int(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_cur_freq", -1)
            if freq > 0:
                info.freq_mhz.append(freq // 1000)
            else:
                break

        info.temp_c = self._cpu_temp()

        # Load ortalamaları
        load = read_proc(f"{PROC}/loadavg").split()
        if len(load) >= 3:
            info.load1, info.load5, info.load15 = (float(x) for x in load[:3])
        return info

    def _cpu_temp(self) -> float | None:
        if not IS_LINUX:
            return None
        base = "/sys/class/thermal"
        if not os.path.isdir(base):
            return None
        for zone in sorted(os.listdir(base)):
            if not zone.startswith("thermal_zone"):
                continue
            zone_type = read_sys(f"{base}/{zone}/type")
            raw = read_int(f"{base}/{zone}/temp", -1)
            if raw <= 0:
                continue
            celsius = raw / 1000.0
            if "cpu" in zone_type.lower() or "soc" in zone_type.lower() or 20.0 < celsius < 120.0:
                return round(celsius, 1)
        return None

    # ------------------------------------------------------------------
    #  BELLEK
    # ------------------------------------------------------------------
    def _memory(self) -> MemoryInfo:
        info = MemoryInfo()
        mem: dict[str, int] = {}
        if PROC:
            for ln in read_proc(f"{PROC}/meminfo").splitlines():
                key, _, rest = ln.partition(":")
                val = rest.split()
                if val and val[0].isdigit():
                    mem[key] = int(val[0])  # kB

        total = mem.get("MemTotal", 0)
        avail = mem.get("MemAvailable", total)
        used = total - avail
        info.total_mb = total // 1024
        info.used_mb = used // 1024
        info.free_mb = mem.get("MemFree", 0) // 1024
        info.cache_mb = (mem.get("Cached", 0) + mem.get("SReclaimable", 0)) // 1024
        info.buffer_mb = mem.get("Buffers", 0) // 1024
        info.available_mb = avail // 1024
        info.pct = (used / total * 100.0) if total else 0.0
        return info

    # ------------------------------------------------------------------
    #  DİSK + eMMC sıcaklığı
    # ------------------------------------------------------------------
    def _disk(self) -> DiskInfo:
        info = DiskInfo()
        if IS_LINUX:
            try:
                st = os.statvfs("/")
                total = st.f_blocks * st.f_frsize
                used = (st.f_blocks - st.f_bfree) * st.f_frsize
                info.root_total_mb = int(total // (1024 * 1024))
                info.root_used_mb = int(used // (1024 * 1024))
                info.root_pct = (used / total * 100.0) if total else 0.0
            except Exception:
                pass
        if self.config.show_emmc:
            info.emmc_temp_c, info.emmc_temp_source = self._emmc_temp()
        return info

    def _emmc_temp(self):
        """eMMC (mmcblk) sıcaklık sensörünü arar, varsa °C döndürür."""
        if not IS_LINUX:
            return None, ""
        for base in ("/sys/class/mmc_host", "/sys/block/mmcblk0/device"):
            if not os.path.isdir(base):
                continue
            for root, _dirs, files in os.walk(base):
                if "temp1_input" in files:
                    raw = read_int(os.path.join(root, "temp1_input"), -1)
                    if raw > 0:
                        return round(raw / 1000.0, 1), os.path.basename(base)
        return None, ""

    # ------------------------------------------------------------------
    #  AĞ
    # ------------------------------------------------------------------
    def _network(self) -> NetworkInfo:
        now = time.monotonic()
        dt = now - self._last_net_ts if self._last_net_ts else 1.0
        self._last_net_ts = now
        if dt <= 0:
            dt = 0.001

        info = NetworkInfo()
        wan = self._wan_info()
        info.wan_ipv4 = wan["ipv4"]
        info.wan_ipv6 = wan["ipv6"]
        info.wan_proto = wan["proto"]
        info.wan_address = wan["address"]
        info.wan_gateway = wan["gateway"]
        info.wan_dns = wan["dns"]

        up = self._up_interfaces()
        text = read_proc(f"{PROC}/net/dev") if PROC else ""
        total_rx = total_tx = 0
        total_rx_rate = total_tx_rate = 0.0

        dev_names = {ln.partition(":")[0].strip() for ln in text.splitlines() if ":" in ln}
        wan_dev = self._resolve_wan_dev(wan["device"], dev_names)

        for ln in text.splitlines():
            if ":" not in ln:
                continue
            name, _, rest = ln.partition(":")
            name = name.strip()
            cols = rest.split()
            if len(cols) < 16:
                continue
            try:
                rx, tx = int(cols[0]), int(cols[8])
            except ValueError:
                continue

            prev = self._prev_net.get(name, (rx, tx))
            rx_rate = max(0.0, (rx - prev[0])) / dt
            tx_rate = max(0.0, (tx - prev[1])) / dt
            self._prev_net[name] = (rx, tx)

            iface = IfaceStat(
                name=name,
                up=name in up,
                rx_bytes=rx,
                tx_bytes=tx,
                rx_rate=rx_rate,
                tx_rate=tx_rate,
                link_mbps=self._link_speed(name),
            )
            iface.ipv4 = self._ip_addr_for(name, 4)
            iface.ipv6 = self._ip_addr_for(name, 6)
            info.interfaces.append(iface)

            # Toplam D/U yalnızca WAN cihazından hesaplanır. Aksi halde PPPoE
            # katmanları (eth1, eth1.35, pppoe-wan) VE br-lan aynı trafiği
            # birden çok sayar; indirirken br-lan.tx de U'ya eklenince D ve U
            # birbirinin kopyası gibi birlikte ilerler.
            if name == wan_dev:
                total_rx += rx
                total_tx += tx
                total_rx_rate += rx_rate
                total_tx_rate += tx_rate

        info.total_rx = total_rx
        info.total_tx = total_tx
        info.total_rx_rate = total_rx_rate
        info.total_tx_rate = total_tx_rate

        # Grafik geçmişi
        self.history_rx.append(total_rx_rate)
        self.history_tx.append(total_tx_rate)
        info.history_rx = list(self.history_rx)
        info.history_tx = list(self.history_tx)

        # Ping + internet (arka plan iş parçacığında ölçülür, UI engellenmez)
        with self._ping_lock:
            info.pings = list(self._ping_results)
        info.internet = bool(info.pings and info.pings[0].alive)
        if info.internet:
            info.internet_latency_ms = info.pings[0].latency_ms

        # Wi-Fi istemcileri
        wifi_clients, wifi_ssid = self._cached("wifi", self._wifi, 4.0)
        info.wifi_clients = wifi_clients
        info.wifi_ssid = wifi_ssid

        # Conntrack
        info.conntrack = self._conntrack()
        info.conntrack_max = read_int(f"{PROC}/sys/net/netfilter/nf_conntrack_max") if PROC else 0

        # LAN cihazları
        info.lan_devices = self._cached("lan_devices", self._lan_devices, 4.0)
        return info

    def _up_interfaces(self) -> set[str]:
        up: set[str] = set()
        base = "/sys/class/net"
        if IS_LINUX and os.path.isdir(base):
            for name in os.listdir(base):
                # "unknown" da arayüzün aktif olduğu anlamına gelebilir
                # (ppp/tun gibi sanal arayüzler operstate=unknown döndürür).
                if read_sys(f"{base}/{name}/operstate") in ("up", "unknown"):
                    up.add(name)
        return up

    def _link_speed(self, iface: str) -> int | None:
        """Ethernet için /sys speed (Mbps); Wi-Fi için iwinfo bitrate."""
        if iface.startswith("wlan"):
            info = run(f"iwinfo {iface} info")
            m = re.search(r"Bit Rate:\s*([\d.]+)\s*MBit/s", info)
            return int(float(m.group(1))) if m else None
        speed = read_int(f"/sys/class/net/{iface}/speed", -1)
        return speed if speed > 0 else None

    def _ip_addr_for(self, iface: str, family: int) -> str:
        out = run(f"ip -{family} addr show dev {iface}")
        m = re.search(r"inet6?\s+([0-9a-fA-F:.]+)/", out)
        return m.group(1) if m else ""

    def _wan_info(self) -> dict:
        """WAN arayüz bilgilerini ubus'tan toplar.

        Döner: ipv4, ipv6, proto, address (ön ekli), gateway, dns, device (l3).
        """
        out = {"ipv4": "", "ipv6": "", "proto": "", "address": "", "gateway": "", "dns": [], "device": ""}
        data = None
        info = run("ubus call network.interface.wan status")
        if info.strip():
            try:
                data = json.loads(info)
            except Exception:
                data = None
        if data:
            out["proto"] = str(data.get("proto") or "")
            out["device"] = str(data.get("l3_device") or data.get("device") or "")
            v4 = data.get("ipv4-address") or []
            if v4:
                addr = v4[0].get("address", "")
                mask = v4[0].get("mask", 0)
                out["ipv4"] = addr
                out["address"] = f"{addr}/{mask}" if addr else ""
            v6 = data.get("ipv6-address") or []
            if v6:
                out["ipv6"] = v6[0].get("address", "")
            for r in data.get("route") or []:
                if r.get("target") in ("0.0.0.0", "::", "default"):
                    gw = r.get("nexthop", "")
                    if gw and gw not in ("0.0.0.0", "::"):
                        out["gateway"] = gw
                        break
            out["dns"] = [str(d) for d in (data.get("dns-server") or []) if d]
        # Yedekler
        if not out["ipv4"]:
            out["ipv4"] = self._ip_addr_for(self.config.wan_interface, 4)
        if not out["ipv6"]:
            out["ipv6"] = self._ip_addr_for(self.config.wan_interface, 6)
        if not out["dns"]:
            for ln in run("cat /tmp/resolv.conf").splitlines():
                m = re.search(r"nameserver\s+([0-9a-fA-F:.]+)", ln)
                if m and m.group(1) not in out["dns"]:
                    out["dns"].append(m.group(1))
        if not out["device"]:
            out["device"] = self.config.wan_interface
        return out

    def _resolve_wan_dev(self, candidate: str, names: set[str]) -> str:
        """Toplam D/U için hangi arayüzün WAN olduğunu belirler."""
        if candidate and candidate in names:
            return candidate
        for cand in ("pppoe-wan", "pppoe0", self.config.wan_interface):
            if cand in names:
                return cand
        # lo/br/docker hariç ilk arayüz
        for n in names:
            if n != "lo" and not n.startswith("br-") and not n.startswith("docker"):
                return n
        return candidate

    def _do_pings(self) -> list[PingResult]:
        results: list[PingResult] = []
        for host in self.config.ping_hosts:
            # -c 2 -W 1: yaklaşık 1 saniyede biter (2 sn zaman aşımına sığar)
            out = run(f"ping -c 2 -W 1 {host}", timeout=3.0)
            loss = 100.0
            m_loss = re.search(r"(\d+(?:\.\d+)?)% packet loss", out)
            if m_loss:
                loss = float(m_loss.group(1))
            latency = 0.0
            m_avg = re.search(r"= [\d.]+/([\d.]+)/[\d.]+ ms", out)
            if m_avg:
                latency = float(m_avg.group(1))
            results.append(
                PingResult(host=host, alive=loss < 100.0, latency_ms=round(latency, 1), loss_pct=loss)
            )
        return results

    def _wifi(self) -> tuple[int, str]:
        total_clients = 0
        ssid = ""
        for iface in self.config.wifi_interfaces:
            info = run(f"iwinfo {iface} info")
            if not info.strip():
                continue
            m = re.search(r'ESSID:\s*"([^"]*)"', info)
            if m and m.group(1):
                ssid = m.group(1)
            assoc = run(f"iwinfo {iface} assoclist")
            total_clients += len(re.findall(r"(?m)^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\s", assoc))
        return total_clients, ssid

    def _conntrack(self) -> int:
        count = read_int(f"{PROC}/sys/net/netfilter/nf_conntrack_count") if PROC else 0
        if count <= 0 and PROC:
            count = read_proc(f"{PROC}/net/nf_conntrack").count("\n")
        return count

    # ------------------------------------------------------------------
    #  LAN CİHAZLARI (ARP + DHCP + conntrack trafiği)
    # ------------------------------------------------------------------
    def _lan_devices(self) -> list[LanDevice]:
        now = time.monotonic()
        dt = now - self._prev_dev_ts if self._prev_dev_ts else 1.0
        self._prev_dev_ts = now
        if dt <= 0:
            dt = 0.001

        # conntrack kümülatif toplamları: ip -> [up(orig), down(reply)]
        cumulative: dict[str, list[int]] = {}
        if PROC:
            text = read_proc(f"{PROC}/net/nf_conntrack")
            for ln in text.splitlines():
                if "ipv4" not in ln:
                    continue
                addrs = re.findall(r"src=([\d.]+) dst=([\d.]+)", ln)
                bytes_ = re.findall(r"bytes=(\d+)", ln)
                if not addrs or len(bytes_) < 2:
                    continue
                src, _dst = addrs[0]
                up, down = int(bytes_[0]), int(bytes_[1])
                cell = cumulative.setdefault(src, [0, 0])
                cell[0] += up
                cell[1] += down

        wan_ipv4 = self._wan_info()["ipv4"]
        rates: dict[str, tuple[float, float]] = {}
        for ip, (up, down) in cumulative.items():
            if ip == wan_ipv4:
                continue  # yönlendiricinin kendi WAN trafiğini atla
            prev = self._prev_dev.get(ip, (up, down))
            up_rate = max(0.0, (up - prev[0])) / dt
            down_rate = max(0.0, (down - prev[1])) / dt
            rates[ip] = (up_rate, down_rate)
        self._prev_dev = cumulative

        # ARP tablosu: ip -> mac
        arp: dict[str, str] = {}
        if PROC:
            for ln in read_proc(f"{PROC}/net/arp").splitlines()[1:]:
                parts = ln.split()
                if len(parts) >= 4 and parts[3] != "00:00:00:00:00:00":
                    arp[parts[0]] = parts[3]

        # DHCP kiralamaları: mac -> hostname ('*' = cihaz adı bildirmemiş)
        leases: dict[str, str] = {}
        for ln in run_list("cat /tmp/dhcp.leases"):
            parts = ln.split()
            if len(parts) >= 4:
                hn = parts[3]
                leases[parts[1]] = "" if hn in ("", "*") else hn

        devices: list[LanDevice] = []
        for ip in set(arp) | set(rates):
            mac = arp.get(ip, "—")
            hostname = leases.get(mac, "") or self._lookup_hostname(ip)
            up_rate, down_rate = rates.get(ip, (0.0, 0.0))
            devices.append(
                LanDevice(ip=ip, mac=mac, hostname=hostname, rx_rate=down_rate, tx_rate=up_rate)
            )
        devices.sort(key=lambda d: d.rx_rate + d.tx_rate, reverse=True)
        return devices

    def _lookup_hostname(self, ip: str) -> str:
        """Kira dosyasında olmayan IP'nin hostname'ini ters DNS ile bulur.

        Sonuçlar önbellekte tutulur (her IP için yalnızca bir kez sorgu).
        """
        if ip in self._hostname_cache:
            return self._hostname_cache[ip]
        name = ""
        out = run(f"nslookup {ip}")
        m = re.search(r"name = ([^\s]+)", out)
        if m:
            name = m.group(1).rstrip(".")
            if name.endswith(".lan"):
                name = name[: -len(".lan")]
        self._hostname_cache[ip] = name
        return name

    # ------------------------------------------------------------------
    #  SERVİSLER
    # ------------------------------------------------------------------
    def _services(self) -> ServiceInfo:
        info = ServiceInfo()

        # Firewall
        nft_rules = run_list("nft list ruleset")
        if len(nft_rules) > 4:
            info.firewall = "Aktif (nftables)"
        else:
            n = len(run_list("iptables -L -n"))
            info.firewall = "Aktif (iptables)" if n > 8 else "Pasif"

        # WireGuard
        wg = run("wg show")
        if wg.strip():
            peers = len(re.findall(r"(?m)^peer:", wg))
            info.wireguard = f"Aktif · {peers} peer"
        else:
            info.wireguard = "Pasif"

        # OpenVPN
        n = len(run_list("pgrep -f openvpn"))
        info.openvpn = f"Aktif ({n})" if n else "Pasif"

        # Passwall / Xray / sing-box
        info.passwall = "Aktif" if run_list("pgrep -f passwall") else "Pasif"
        info.xray = "Aktif" if run_list("pgrep -f xray") else "Pasif"
        info.singbox = "Aktif" if run_list("pgrep -f sing-box") else "Pasif"

        # AdGuard Home
        info.adguard = "Aktif" if run_list("pgrep -f AdGuardHome") else "Pasif"

        # DNS sorgu sayısı (port 53 conntrack girişi)
        info.dns_queries = self._dns_queries()

        # Docker
        info.docker_running, info.docker_containers = self._cached("docker", self._docker, 10.0)
        return info

    def _dns_queries(self) -> int:
        if not PROC:
            return 0
        text = read_proc(f"{PROC}/net/nf_conntrack")
        return sum(1 for ln in text.splitlines() if "dport=53" in ln or "sport=53" in ln)

    def _docker(self):
        containers: list[DockerContainer] = []
        ps = run("docker ps --format '{{.Names}}|{{.Status}}'")
        if not ps.strip():
            return False, containers
        for ln in ps.splitlines():
            parts = ln.split("|", 1)
            if len(parts) == 2:
                containers.append(DockerContainer(name=parts[0].strip(), status=parts[1].strip()))

        stats = run("docker stats --no-stream --format '{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}'")
        stat_map = {c.name: c for c in containers}
        for ln in stats.splitlines():
            parts = ln.split("|")
            if len(parts) != 3:
                continue
            container = stat_map.get(parts[0].strip())
            if not container:
                continue
            m_cpu = re.search(r"([\d.]+)\s*%", parts[1])
            if m_cpu:
                container.cpu_pct = float(m_cpu.group(1))
            m_mem = re.search(r"([\d.]+)([KMGT]i?B)\s*/\s*([\d.]+)([KMGT]i?B)?", parts[2])
            if m_mem:
                container.mem_used_mb = self._to_mib(float(m_mem.group(1)), m_mem.group(2))
                container.mem_limit_mb = self._to_mib(float(m_mem.group(3)), m_mem.group(4) or "B")
        return True, containers

    @staticmethod
    def _to_mib(value: float, unit: str) -> float:
        unit = unit.upper()
        if unit.startswith("K"):
            return value / 1024
        if unit.startswith("M"):
            return value
        if unit.startswith("G"):
            return value * 1024
        if unit.startswith("T"):
            return value * 1024 * 1024
        return value / 1024 / 1024  # B -> MiB

    # ------------------------------------------------------------------
    #  LOGLAR
    # ------------------------------------------------------------------
    def _logs(self) -> list[LogEntry]:
        out = run("logread -l 30")
        pattern = re.compile(r"\b(err|error|fail|failed|crit|alert|panic|warn)\b|daemon\.err|kern\.err", re.I)
        entries: list[LogEntry] = []
        for ln in out.splitlines()[-self.config.log_lines:]:
            entries.append(LogEntry(line=ln, is_error=bool(pattern.search(ln))))
        return entries
