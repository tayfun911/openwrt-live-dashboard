"""Docker paneli: konteyner listesi + CPU/RAM kullanımı."""
from __future__ import annotations

from .base import Panel, COL_LABEL, COL_VALUE


class DockerPanel(Panel):
    def __init__(self, **kwargs) -> None:
        super().__init__("Docker", **kwargs)

    def update_data(self, snap) -> None:
        services = snap.services
        if not services.docker_running:
            self.update("[dim]Docker calismiyor veya kurulu degil.[/]")
            return

        lines = [f"[bold {COL_LABEL}]{len(services.docker_containers)} konteyner[/]"]
        for container in services.docker_containers:
            lines.append(
                f"{container.name:<20} "
                f"[{COL_LABEL}]{'CPU':<4}[/][bold {COL_VALUE}]{container.cpu_pct:5.1f}%[/]  "
                f"[{COL_LABEL}]{'RAM':<4}[/][bold {COL_VALUE}]{container.mem_used_mb:6.1f}/{container.mem_limit_mb:.1f} GiB[/]  "
                f"[dim]{container.status}[/]"
            )
        self.update("\n".join(lines))
