class MemoryLeaker:
    def __init__(self):
        # Глобальный список, который не очищается сборщиком мусора
        self._leaked_data = []

    def leak(self, size_mb: int = 1) -> int:
        """
        Эмулирует утечку памяти, добавляя строку заданного размера в список.
        Возвращает общий объем 'утекшей' памяти в мегабайтах.
        """
        # Генерируем строку нужного размера (1 символ = 1 байт в ASCII)
        chunk = " " * (size_mb * 1024 * 1024)
        self._leaked_data.append(chunk)

        return len(self._leaked_data) * size_mb


# Инициализируем глобальный объект для сохранения состояния между HTTP-запросами
memory_leaker = MemoryLeaker()