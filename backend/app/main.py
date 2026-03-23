import asyncio
import time
from fastapi import FastAPI, Request
from .api import router

app = FastAPI(title="VAK Load Testing API")


@app.middleware("http")
async def measure_event_loop_lag(request: Request, call_next):
    start_time = time.time()

    # Передаем управление циклу событий.
    # Если цикл перегружен заблокированными задачами,
    # возвращение обратно займет аномально много времени.
    await asyncio.sleep(0)
    lag = time.time() - start_time

    # Обрабатываем запрос
    response = await call_next(request)

    # Добавляем нашу метрику прямо в HTTP-заголовки ответа,
    # чтобы её можно было вытащить при анализе
    response.headers["X-Event-Loop-Lag"] = str(lag)
    return response


app.include_router(router)