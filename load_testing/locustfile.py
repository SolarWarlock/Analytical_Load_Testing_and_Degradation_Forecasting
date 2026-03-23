from locust import HttpUser, task, between

class DegradationUser(HttpUser):
    # Имитация реального поведения: пользователь "думает" от 0.1 до 0.5 секунд между запросами
    wait_time = between(0.1, 0.5)

    @task(100)
    def normal_workload(self):
        """
        Основная бизнес-логика. 
        Вес 100 означает, что этот запрос будет выполняться в 100 раз чаще.
        Именно по этому эндпоинту мы будем замерять 95-й перцентиль (p95) 
        и падение RPS, когда сервер начнет задыхаться.
        """
        # Параметр name группирует статистику в отчетах Locust
        self.client.get("/workload/normal", name="1_Normal_Workload")

    @task(1)
    def trigger_leak(self):
        """
        Фоновая деградация.
        Вес 1 означает, что запрос выполняется редко. При каждом вызове
        он "откусывает" 5 Мб от нашей ограниченной в Docker оперативной памяти.
        """
        # Передаем параметр size_mb=5
        self.client.post("/degradation/memory?size_mb=5", name="2_Trigger_Leak")