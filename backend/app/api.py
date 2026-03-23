import asyncio
from fastapi import APIRouter
from .degradation.memory_leak import memory_leaker

router = APIRouter()

@router.get("/health")
async def health_check():
    """Здоровый эндпоинт для проверки базовой реактивности системы."""
    return {"status": "ok", "message": "Server is running"}

@router.get("/workload/normal")
async def normal_workload():
    """Эмуляция полезной работы бэкенда (например, легкий запрос к БД)."""
    # Асинхронная пауза имитирует время ожидания I/O операций
    await asyncio.sleep(0.05)
    return {"status": "success", "data": "processed"}

@router.post("/degradation/memory")
async def trigger_memory_leak(size_mb: int = 5):
    """
    Эндпоинт-триггер. При каждом вызове забивает память на size_mb мегабайт.
    """
    total_leaked = memory_leaker.leak(size_mb)
    return {
        "status": "degraded",
        "message": f"Leaked additional {size_mb}MB",
        "total_leaked_mb": total_leaked
    }