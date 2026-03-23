from fastapi import APIRouter
import asyncio
from .degradation.memory_leak import memory_leaker
from .degradation.slowdown import slowdown_manager  # Подключаем новый модуль

router = APIRouter()


@router.get("/workload/normal")
async def normal_workload():
    """Эмуляция полезной работы бэкенда."""
    # Применяем накопившуюся деградацию времени отклика
    slowdown_manager.apply_delay()

    await asyncio.sleep(0.05)
    return {"status": "success", "data": "processed"}


@router.post("/degradation/slowdown")
async def trigger_slowdown(step: float = 0.02):
    """Каждый вызов увеличивает синхронную задержку на step секунд."""
    new_delay = slowdown_manager.increase_delay(step)
    return {"status": "degraded", "current_blocking_delay": new_delay}