from locust import HttpUser, task, between, events
import csv
import os

# Подготавливаем отдельный файл для записи нашей 7-й метрики (Event Loop Lag)
LAG_LOG_FILE = "load_testing/raw_data/event_loop_lag.csv"


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Создает файл с заголовками при старте теста."""
    os.makedirs(os.path.dirname(LAG_LOG_FILE), exist_ok=True)
    with open(LAG_LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "endpoint", "event_loop_lag_sec"])


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, start_time, url,
               **kwargs):
    """Перехватчик: вытаскивает внутреннюю метрику задержки из ответа FastAPI."""
    if response and hasattr(response, 'headers'):
        lag = response.headers.get("X-Event-Loop-Lag")
        if lag:
            with open(LAG_LOG_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                # Сохраняем метрику для датасета
                writer.writerow([start_time, name, lag])


class DegradationUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(1000)
    def normal_workload(self):
        """Основная полезная нагрузка."""
        self.client.get("/workload/normal", name="1_Normal_Workload")

    @task(2)  # Слегка увеличили частоту вызова
    def trigger_leak(self):
        """Ускоренная утечка памяти: теперь по 8 МБ за раз."""
        self.client.post("/degradation/memory?size_mb=8", name="2_Trigger_Leak")

    @task(1)
    def trigger_slowdown(self):
        """Новая деградация: постепенно блокирует процессор (увеличивает задержку на 1 мс)."""
        self.client.post("/degradation/slowdown?step=0.001", name="3_Trigger_Slowdown")