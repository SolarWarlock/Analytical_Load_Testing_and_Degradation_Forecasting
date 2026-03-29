from locust import HttpUser, task, between, events, LoadTestShape
import csv
import os
import random

LAG_LOG_FILE = "load_testing/raw_data/event_loop_lag.csv"


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    os.makedirs(os.path.dirname(LAG_LOG_FILE), exist_ok=True)
    with open(LAG_LOG_FILE, 'w', newline='') as f:
        csv.writer(f).writerow(["timestamp", "endpoint", "event_loop_lag_sec"])


@events.request.add_listener
def on_request(response_time, response, start_time, name, **kwargs):
    if response and hasattr(response, 'headers'):
        lag = response.headers.get("X-Event-Loop-Lag")
        if lag:
            with open(LAG_LOG_FILE, 'a', newline='') as f:
                csv.writer(f).writerow([start_time, name, lag])


class DegradationUser(HttpUser):
    wait_time = between(0.5, 1.5)

    # Вероятность 10000. Это 99.9% всего трафика.
    @task(10000)
    def normal_workload(self):
        self.client.get("/workload/normal", name="1_Normal_Workload")

    # Вероятность 5. Вызывается очень редко.
    # Отправляем int, чтобы FastAPI не ругался (422 error).
    # Итоговая утечка составит примерно 2-3 МБ в минуту.
    @task(5)
    def trigger_leak(self):
        self.client.post("/degradation/memory?size_mb=1", name="2_Trigger_Leak")

    # Вероятность 5. Замедляет Event Loop по чуть-чуть.
    @task(5)
    def trigger_slowdown(self):
        self.client.post("/degradation/slowdown?step=0.00005", name="3_Trigger_Slowdown")


class FluctuatingLoadShape(LoadTestShape):
    base_users = 200
    ramp_up_time = 600
    ramp_up_spawn_rate = 1

    fluctuation_interval = 30
    fluctuation_range = (-20, 20)

    # ЖЕСТКИЙ ЛИМИТ ВРЕМЕНИ: 45 минут (в секундах)
    time_limit = 45 * 60

    def __init__(self):
        super().__init__()
        self.current_target = 0
        self.last_fluctuation_time = 0

    def tick(self):
        run_time = self.get_run_time()

        # --- ИСПРАВЛЕНИЕ: ОСТАНОВКА ТЕСТА ---
        if run_time > self.time_limit:
            return None  # Эта команда глушит Locust

        if run_time < self.ramp_up_time:
            target = int((run_time / self.ramp_up_time) * self.base_users)
            return (target, self.ramp_up_spawn_rate)

        if run_time - self.last_fluctuation_time > self.fluctuation_interval:
            delta = random.randint(self.fluctuation_range[0], self.fluctuation_range[1])
            self.current_target = self.base_users + delta
            self.last_fluctuation_time = run_time

        return (self.current_target, 20)