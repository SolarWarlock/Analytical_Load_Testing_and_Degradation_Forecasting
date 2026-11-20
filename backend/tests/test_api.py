import os
import sys
from types import SimpleNamespace

import pytest
from fastapi import Response

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.api import health_check, normal_workload
    from app.main import app, measure_event_loop_lag, metrics
except ImportError:
    from backend.app.api import health_check, normal_workload
    from backend.app.main import app, measure_event_loop_lag, metrics


def test_app_initialization():
    """Проверка корректной инициализации FastAPI приложения."""
    assert app.title == "VAK Load Testing API"


@pytest.mark.anyio
async def test_health_check_endpoint():
    """Проверка базового health check эндпоинта."""
    result = await health_check()
    assert result["status"] == "ok"
    assert result["message"] == "Server is running"


@pytest.mark.anyio
async def test_normal_workload_endpoint():
    """Проверка эндпоинта нормальной нагрузки."""
    result = await normal_workload()
    assert result["status"] == "success"
    assert result["data"] == "processed"


@pytest.mark.anyio
async def test_middleware_sets_header_and_records_prometheus_metrics():
    """Проверка записи лага в заголовок X-Event-Loop-Lag и в метрики Prometheus."""
    fake_request = SimpleNamespace(
        method="GET",
        url=SimpleNamespace(path="/workload/normal"),
        scope={"route": SimpleNamespace(path="/workload/normal")},
    )

    async def fake_call_next(_request):
        return Response(content='{"status":"success"}', status_code=200)

    response = await measure_event_loop_lag(fake_request, fake_call_next)
    assert "X-Event-Loop-Lag" in response.headers
    assert float(response.headers["X-Event-Loop-Lag"]) >= 0.0

    metrics_response = await metrics()
    body = metrics_response.body.decode("utf-8")
    assert metrics_response.status_code == 200
    assert "fastapi_event_loop_lag_seconds_bucket" in body
    assert "fastapi_event_loop_lag_current_seconds" in body
    assert 'http_requests_total{endpoint="/workload/normal",method="GET",status="200"}' in body
    assert "http_request_duration_seconds_bucket" in body
    assert "degradation_leaked_memory_bytes" in body
    assert "degradation_blocking_delay_seconds" in body
