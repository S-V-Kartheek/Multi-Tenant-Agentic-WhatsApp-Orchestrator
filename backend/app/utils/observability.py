"""
utils/observability.py — Lightweight in-process metrics for Prometheus scraping.

Tracks request counts + latency histograms and agent run outcomes.
Exposes a /metrics endpoint returning Prometheus text format.

This is intentionally dependency-free (no prometheus_client) to keep the
container lean. In a larger deployment you'd swap this for the official client
or ship structured logs to OpenTelemetry — the surface area stays the same.
"""
import time
from collections import defaultdict
from threading import Lock

from fastapi import Request, Response


class _MetricsRegistry:
    """Thread-safe in-process metrics store."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.request_count: dict[str, int] = defaultdict(int)
        self.request_latency_sum: dict[str, float] = defaultdict(float)
        self.request_latency_count: dict[str, int] = defaultdict(int)
        self.agent_runs_total: dict[str, int] = defaultdict(int)  # by status
        self.messages_total: dict[str, int] = defaultdict(int)    # by direction
        self.broadcasts_total: int = 0
        self.start_time = time.time()

    def record_request(self, path: str, duration_sec: float) -> None:
        with self._lock:
            self.request_count[path] += 1
            self.request_latency_sum[path] += duration_sec
            self.request_latency_count[path] += 1

    def record_agent_run(self, status: str) -> None:
        with self._lock:
            self.agent_runs_total[status] += 1

    def record_message(self, direction: str) -> None:
        with self._lock:
            self.messages_total[direction] += 1

    def record_broadcast(self) -> None:
        with self._lock:
            self.broadcasts_total += 1

    def render_prometheus(self) -> str:
        """Render the registry as Prometheus text exposition format."""
        lines: list[str] = []
        uptime = time.time() - self.start_time

        lines.append("# HELP app_uptime_seconds Seconds since the process started.")
        lines.append("# TYPE app_uptime_seconds gauge")
        lines.append(f"app_uptime_seconds {uptime:.2f}")

        lines.append("# HELP http_requests_total Total HTTP requests by path.")
        lines.append("# TYPE http_requests_total counter")
        with self._lock:
            for path, count in sorted(self.request_count.items()):
                lines.append(f'http_requests_total{{path="{path}"}} {count}')

            lines.append("# HELP http_request_duration_seconds_avg Avg duration per path.")
            lines.append("# TYPE http_request_duration_seconds_avg gauge")
            for path in sorted(self.request_latency_sum.keys()):
                avg = self.request_latency_sum[path] / max(self.request_latency_count[path], 1)
                lines.append(f'http_request_duration_seconds_avg{{path="{path}"}} {avg:.6f}')

            lines.append("# HELP agent_runs_total Total agent runs by outcome status.")
            lines.append("# TYPE agent_runs_total counter")
            for status, count in sorted(self.agent_runs_total.items()):
                lines.append(f'agent_runs_total{{status="{status}"}} {count}')

            lines.append("# HELP messages_total Total messages by direction.")
            lines.append("# TYPE messages_total counter")
            for direction, count in sorted(self.messages_total.items()):
                lines.append(f'messages_total{{direction="{direction}"}} {count}')

            lines.append("# HELP broadcasts_total Total broadcast campaigns sent.")
            lines.append("# TYPE broadcasts_total counter")
            lines.append(f"broadcasts_total {self.broadcasts_total}")

        return "\n".join(lines) + "\n"


# Module-level singleton
metrics = _MetricsRegistry()


async def metrics_middleware(request: Request, call_next):
    """FastAPI/Starlette middleware: time every request and record it."""
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration = time.perf_counter() - start

    # Only record API routes (skip /metrics itself to avoid self-inflation)
    path = request.url.path
    if path.startswith("/api") or path in ("/", "/health"):
        metrics.record_request(path, duration)

    return response


def render_metrics() -> str:
    """Render current metrics — called by the /metrics endpoint handler."""
    return metrics.render_prometheus()
