from fastapi import FastAPI
from .api import router

# Инициализируем приложение с метаданными (полезно для автогенерации документации Swagger)
app = FastAPI(
    title="VAK Load Testing API",
    description="Стенд для аналитического нагрузочного тестирования и моделирования деградации.",
    version="1.0.0"
)

# Подключаем наши маршруты
app.include_router(router)