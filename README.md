# High-Performance FastAPI: Диагностика и профилирование Event Loop под нагрузкой

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Uvicorn](https://img.shields.io/badge/ASGI-Uvicorn-2C5BB4.svg)](https://www.uvicorn.org/)
[![Docker](https://img.shields.io/badge/Docker-cgroups_v2-2496ED.svg)](https://www.docker.com/)
[![Locust](https://img.shields.io/badge/Load_Testing-Locust-green.svg)](https://locust.io/)

Бэкенд на FastAPI с кастомным middleware для замера лагов цикла событий (Event Loop) под высокой конкурентной нагрузкой.

---

## 🎯 О чем проект

Главная уязвимость асинхронных веб-приложений — блокировка общего цикла событий. Достаточно одной тяжелой синхронной функции или утечки памяти, чтобы Uvicorn перестал вовремя отдавать управление ожидающим корутинам.

Внешний мониторинг замечает проблему слишком поздно. Очередь запросов переполняется, а задержка p95 взлетает лавинообразно. 

Проект реализует механизм внутреннего профилирования FastAPI. Сервер самостоятельно замеряет микрозадержки планировщика и передает телеметрию клиенту прямо в HTTP-заголовках ответа.

---

## ⚙️ Ключевые решения в бэкенде

### 1. Перехват лага цикла событий через ASGI Middleware
Кастомный middleware замеряет время, за которое планировщик Python возвращает управление корутине:

```python
@app.middleware("http")
async def measure_event_loop_lag(request: Request, call_next):
    start_time = time.time()

    # Уступаем квант времени планировщику
    # При перегрузке цикла возврат задерживается
    await asyncio.sleep(0)
    lag = time.time() - start_time

    response = await call_next(request)
    response.headers["X-Event-Loop-Lag"] = str(lag)
    return response
```

Метрика не требует внешних агентов сбора. Клиент или балансировщик сразу видят внутреннее состояние исполнителя в заголовке `X-Event-Loop-Lag`.

### 2. Модульная архитектура роутера
Эндпоинты разделены по назначению через `APIRouter`:

| Метод | Эндпоинт | Назначение |
| :--- | :--- | :--- |
| `GET` | `/health` | Базовый health-check реактивности сервиса |
| `GET` | `/workload/normal` | Асинхронная полезная нагрузка (`asyncio.sleep`) |
| `POST` | `/degradation/memory` | Имитация утечки памяти через накопление байтовых массивов |
| `POST` | `/degradation/slowdown` | Имитация синхронных CPU-блокировок в основном потоке |

### 3. Стресс-тестирование сервиса в Locust
Генератор генерирует стохастический поток от 200 пользователей. Профиль нагрузки эмулирует реальный трафик: 99.9% штатных вызовов и редкие фоновые сбои. Сценарий собирает сквозную статистику клиентских задержек и значений `X-Event-Loop-Lag`.

### 4. Контейнеризация с лимитами cgroups
Сервис развернут в Docker на базе легкого образа `python:3.11-slim`. Для воспроизводимости тестов выделены строгие аппаратные квоты: 1 ядро CPU и 1536 МБ оперативной памяти.

---

## 📊 Результаты профилирования и аналитика

Совместный анализ логов Locust, счетчиков Docker и метрики `X-Event-Loop-Lag` показал четкую картину:

- **Ранний сигнал деградации.** Внутренний лаг цикла событий подскакивает за 40–50 секунд до роста ошибок HTTP 5xx.
- **Поведение под нагрузкой.** Сервис стабильно держит поток до момента блокировки потока или исчерпания буфера памяти.
- **Валидация гипотезы.** Аналитический классификатор на базе собранного датасета подтвердил точность метрики (ROC-AUC 0.97 при нуле ложных срабатываний).

### Динамика задержки и памяти перед отказом
На графике видно, как накопление утечки памяти и блокировок приводит к взрывному росту задержки p95:

![Динамика метрик перед отказом](analytics/figure_4_raw_metrics.png)

---

## 📁 Структура репозитория

```text
├── backend/
│   ├── app/
│   │   ├── api.py                  # Роутер FastAPI и обработчики запросов
│   │   ├── degradation/            # Модули эмуляции утечек RAM и лагов CPU
│   │   │   ├── memory_leak.py      # Управляемое накопление памяти
│   │   │   └── slowdown.py         # Эмуляция задержек обработки
│   │   └── main.py                 # Инициализация FastAPI и ASGI-middleware
│   ├── Dockerfile                  # Оптимизированный образ Python 3.11
│   └── requirements.txt            # Зависимости сервиса (FastAPI, Uvicorn)
├── load_testing/
│   ├── locustfile.py               # Сценарий нагрузки и профиль 200 пользователей
│   └── system_monitor.py           # Посекундная телеметрия хоста
├── infrastructure/
│   └── docker-compose.yml          # Запуск сервиса с квотами ресурсов
├── analytics/                      # Анализ телеметрии и проверка гипотез
├── docs/                           # Протоколы нагрузочных прогонов
├── run_load_test.ps1               # Запуск стресс-теста Locust
└── start_monitoring.ps1            # Сбор системной телеметрии контейнера
```

---

## 🚀 Локальный запуск и проверка

### 1. Запуск через Docker Compose (рекомендуется)

```bash
cd infrastructure
docker compose up -d --build
```

Сервер доступен по адресу `http://localhost:8000`. Документация Swagger UI открывается на `http://localhost:8000/docs`.

### 2. Запуск напрямую через Python

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Для Linux/macOS
# .\.venv\Scripts\Activate.ps1  # Для Windows
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Проверка работы middleware

Отправьте тестовый запрос и проверьте заголовок лага:

```bash
curl -i http://localhost:8000/workload/normal
```

В ответе придет заголовок `X-Event-Loop-Lag`:

```http
HTTP/1.1 200 OK
content-type: application/json
x-event-loop-lag: 0.00010204315185546875
content-length: 39
```

### 4. Запуск нагрузочного теста Locust

Установите Locust и запустите сценарий:

```bash
pip install locust
locust -f load_testing/locustfile.py --host http://localhost:8000
```

Веб-интерфейс генератора откроется на `http://localhost:8089`.

---

## 🛠 Технологический стек бэкенда

- **Язык:** Python 3.11 / 3.13 (асинхронные возможности, типизация Pydantic).
- **Фреймворк:** FastAPI (высокая скорость, валидация данных, автогенерация OpenAPI).
- **Сервер:** Uvicorn (ASGI-сервер на базе uvloop и httptools).
- **Тестирование нагрузки:** Locust (сценарное моделирование пользователей).
- **Среда запуска:** Docker Compose (cgroups v2, строгий контроль ресурсов).