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
    wait_time = between(0.1, 0.5)

    @task(1000)
    def normal_workload(self):
        self.client.get("/workload/normal", name="1_Normal_Workload")

    @task(2)
    def trigger_leak(self):
        # Оставили 1 МБ для плавной утечки
        self.client.post("/degradation/memory?size_mb=1", name="2_Trigger_Leak")

    @task(1)
    def trigger_slowdown(self):
        # Оставили 0.2 мс для плавной блокировки Event Loop
        self.client.post("/degradation/slowdown?step=0.0002", name="3_Trigger_Slowdown")


# Класс стохастической нагрузки ОБЯЗАТЕЛЬНО должен быть в этом же файле
class FluctuatingLoadShape(LoadTestShape):
    base_users = 200
    ramp_up_time = 120
    ramp_up_spawn_rate = 2
    fluctuation_interval = 15
    fluctuation_range = (-15, 15)

    def __init__(self):
        super().__init__()
        self.current_target = 0
        self.last_fluctuation_time = 0

    def tick(self):
        run_time = self.get_run_time()
        if run_time < self.ramp_up_time:
            target = int((run_time / self.ramp_up_time) * self.base_users)
            return (target, self.ramp_up_spawn_rate)

        if run_time - self.last_fluctuation_time > self.fluctuation_interval:
            delta = random.randint(self.fluctuation_range[0], self.fluctuation_range[1])
            self.current_target = self.base_users + delta
            self.last_fluctuation_time = run_time

        return (self.current_target, 20)