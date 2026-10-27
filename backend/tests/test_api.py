import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.main import app
    from app.api import health_check, normal_workload
except ImportError:
    from backend.app.main import app
    from backend.app.api import health_check, normal_workload


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
