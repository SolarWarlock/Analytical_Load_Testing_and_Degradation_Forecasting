import asyncio
from fastapi import APIRouter
from .degradation.memory_leak import memory_leaker
from .degradation.slowdown import slowdown_manager

router = APIRouter()


@router.get("/health")
async def health_check():
    """Здоровый эндпоинт для проверки базовой реактивности системы."""
    return {"status": "ok", "message": "Server is running"}


@router.get("/workload/normal")
async def normal_workload():
    """Эмуляция полезной работы бэкенда."""
    # Применяем накопившуюся деградацию времени отклика (CPU/I/O lag)
    slowdown_manager.apply_delay()

    await asyncio.sleep(0.05)
    return {"status": "success", "data": "processed"}


@router.post("/degradation/memory")
async def trigger_memory_leak(size_mb: int = 5):
    """Эндпоинт-триггер. При каждом вызове забивает оперативную память."""
    total_leaked = memory_leaker.leak(size_mb)
    return {
        "status": "degraded",
        "message": f"Leaked additional {size_mb}MB",
        "total_leaked_mb": total_leaked
    }


@router.post("/degradation/slowdown")
async def trigger_slowdown(step: float = 0.02):
    """Эндпоинт-триггер. При каждом вызове увеличивает задержку обработки."""
    new_delay = slowdown_manager.increase_delay(step)
    return {"status": "degraded", "current_blocking_delay": new_delay}