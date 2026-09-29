"""Veri modelleri — sistem anlık görüntüsü (snapshot)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CpuInfo:
    total: float = 0.0
    cores: list[float] = field(default_factory=list)
    freq_mhz: list[int] = field(default_factory=list)
    temp_c: float | None = None
    load1: float = 0.0
    load5: float = 0.0
    load15: float = 0.0


@dataclass
class MemoryInfo:
    total_mb: int = 0
    used_mb: int = 0
    free_mb: int = 0
    cache_mb: int = 0
    buffer_mb: int = 0
    available_mb: int = 0
    pct: float = 0.0


@dataclass
class DiskInfo:
    root_total_mb: int = 0
    root_used_mb: int = 0
    root_pct: float = 0.0
    emmc_temp_c: float | None = None
    emmc_temp_source: str = ""


@dataclass
class IfaceStat:
    name: str
    up: bool
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_rate: float = 0.0     # byte/sn
    tx_rate: float = 0.0     # byte/sn
    link_mbps: int | None = None
    ipv4: str = ""
    ipv6: str = ""


@dataclass
class PingResult:
    host: str
    alive: bool
    latency_ms: float = 0.0
    loss_pct: float = 100.0


@dataclass
class LanDevice:
    ip: str
    mac: str
    hostname: str
    rx_rate: float = 0.0     # byte/sn (indirme)
    tx_rate: float = 0.0     # byte/sn (yükleme)


@dataclass
class DockerContainer:
    name: str
    status: str
    cpu_pct: float = 0.0
    mem_used_mb: float = 0.0
    mem_limit_mb: float = 0.0


@dataclass
class NetworkInfo:
    wan_ipv4: str = ""
    wan_ipv6: str = ""
    wan_proto: str = ""          # ör. pppoe
    wan_address: str = ""        # ör. 100.76.82.173/32
    wan_gateway: str = ""        # ör. 195.87.128.164
    wan_dns: list[str] = field(default_factory=list)  # ör. 195.46.155.11
    interfaces: list[IfaceStat] = field(default_factory=list)
    pings: list[PingResult] = field(default_factory=list)
    internet: bool = False
    internet_latency_ms: float = 0.0
    wifi_clients: int = 0
    wifi_ssid: str = ""
    lan_devices: list[LanDevice] = field(default_factory=list)
    conntrack: int = 0
    conntrack_max: int = 0
    total_rx: int = 0
    total_tx: int = 0
    total_rx_rate: float = 0.0
    total_tx_rate: float = 0.0
    history_rx: list[float] = field(default_factory=list)
    history_tx: list[float] = field(default_factory=list)


@dataclass
class ServiceInfo:
    firewall: str = "—"
    wireguard: str = "—"
    openvpn: str = "—"
    passwall: str = "—"
    xray: str = "—"
    singbox: str = "—"
    adguard: str = "—"
    dns_queries: int = 0
    docker_running: bool = False
    docker_containers: list[DockerContainer] = field(default_factory=list)


@dataclass
class LogEntry:
    line: str
    is_error: bool = False


@dataclass
class SystemSnapshot:
    cpu: CpuInfo = field(default_factory=CpuInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    disk: DiskInfo = field(default_factory=DiskInfo)
    network: NetworkInfo = field(default_factory=NetworkInfo)
    services: ServiceInfo = field(default_factory=ServiceInfo)
    uptime_s: float = 0.0
    kernel: str = ""
    openwrt_version: str = ""
    hostname: str = ""
    datetime_str: str = ""
    logs: list[LogEntry] = field(default_factory=list)
    errors: int = 0
