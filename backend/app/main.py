import asyncio
import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .api import router
from .metrics import (
    EVENT_LOOP_LAG_CURRENT_SECONDS,
    EVENT_LOOP_LAG_SECONDS,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)

app = FastAPI(title="VAK Load Testing API")


def _resolve_endpoint_label(request: Request) -> str:
    """Возвращает шаблон маршрута вместо сырого URL для защиты от high cardinality."""
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return "unmatched"


@app.middleware("http")
async def measure_event_loop_lag(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    lag_start = time.perf_counter()

    # Передаем управление циклу событий.
    # Если цикл перегружен заблокированными задачами,
    # возвращение обратно займет аномально много времени.
    await asyncio.sleep(0)
    lag = time.perf_counter() - lag_start

    EVENT_LOOP_LAG_SECONDS.observe(lag)
    EVENT_LOOP_LAG_CURRENT_SECONDS.set(lag)

    request_start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    finally:
        duration = time.perf_counter() - request_start
        endpoint = _resolve_endpoint_label(request)
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(status_code),
        ).inc()

    # Дублируем метрику в HTTP-заголовок ответа для сценариев Locust и CSV-выгрузок
    response.headers["X-Event-Loop-Lag"] = str(lag)
    return response


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Экспортирует метрики приложения в формате Prometheus (pull-модель)."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(router)