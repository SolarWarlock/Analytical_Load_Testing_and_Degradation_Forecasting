import time

class SlowdownManager:
    def __init__(self):
        self.delay_sec = 0.0

    def increase_delay(self, step: float = 0.01):
        """Увеличивает синхронную задержку, эмулируя тяжелые вычисления или долгую БД."""
        self.delay_sec += step
        return self.delay_sec

    def apply_delay(self):
        if self.delay_sec > 0:
            # ВАЖНО: time.sleep() — это синхронная блокировка.
            # Она застопорит весь Event Loop сервера.
            time.sleep(self.delay_sec)

slowdown_manager = SlowdownManager()