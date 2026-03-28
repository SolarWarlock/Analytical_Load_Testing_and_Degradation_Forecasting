from locust import LoadTestShape
import random
import time


class FluctuatingLoadShape(LoadTestShape):
    """
    Кастомный профиль стохастической нагрузки для эмуляции реального трафика.
    """
    # --- НАСТРОЙКИ ПРОФИЛЯ ---
    base_users = 200  # Базовый пик пользователей
    ramp_up_time = 120  # Время (в секундах) для плавного выхода на пик (например, 2 минуты)
    ramp_up_spawn_rate = 2  # С какой скоростью добавлять пользователей при разогреве

    fluctuation_interval = 15  # Как часто меняем нагрузку (каждые 15 секунд)
    fluctuation_range = (-15, 15)  # Диапазон случайного отклонения от базового пика

    def __init__(self):
        super().__init__()
        self.current_target = 0
        self.last_fluctuation_time = 0

    def tick(self):
        """Эта функция вызывается Locust каждую секунду для определения нужного числа юзеров."""
        run_time = self.get_run_time()

        # ФАЗА 1: Плавный разогрев (Ramp-up)
        if run_time < self.ramp_up_time:
            # Линейно высчитываем, сколько юзеров должно быть сейчас
            target = int((run_time / self.ramp_up_time) * self.base_users)
            return (target, self.ramp_up_spawn_rate)

        # ФАЗА 2: Стохастическое колебание на пике (Fluctuation)
        # Если с момента последнего изменения прошло больше fluctuation_interval секунд:
        if run_time - self.last_fluctuation_time > self.fluctuation_interval:
            # Генерируем случайное отклонение (например, от -15 до +15)
            delta = random.randint(self.fluctuation_range[0], self.fluctuation_range[1])
            # Устанавливаем новую цель
            self.current_target = self.base_users + delta
            # Запоминаем время изменения
            self.last_fluctuation_time = run_time

        # Возвращаем текущую цель и высокую скорость спавна,
        # чтобы Locust быстро подстроил число юзеров (убил или создал новых)
        return (self.current_target, 20)