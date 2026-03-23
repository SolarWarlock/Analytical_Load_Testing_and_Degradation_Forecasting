import psutil
import csv
import time
from datetime import datetime
import os


def start_monitoring(output_path="raw_data/system_metrics.csv", interval_sec=1):
    # Убедимся, что директория существует
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Начинаем сбор системных метрик...")
    print(f"Данные записываются в: {output_path}")
    print("Для остановки нажмите Ctrl+C")

    with open(output_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Заголовки колонок для будущего датасета
        writer.writerow(["timestamp", "cpu_usage_percent", "memory_used_mb", "memory_percent"])

        try:
            # Инициализация для более точного первого замера CPU
            psutil.cpu_percent(interval=None)

            while True:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Замеряем общую загрузку процессора
                cpu_percent = psutil.cpu_percent(interval=None)

                # Замеряем потребление оперативной памяти
                memory = psutil.virtual_memory()
                memory_used_mb = memory.used / (1024 * 1024)

                # Записываем строку в CSV
                writer.writerow([
                    timestamp,
                    cpu_percent,
                    round(memory_used_mb, 2),
                    memory.percent
                ])

                # Принудительно сбрасываем буфер на диск, чтобы не потерять
                # данные при резком падении системы
                file.flush()

                time.sleep(interval_sec)

        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Мониторинг завершен. Данные сохранены.")


if __name__ == "__main__":
    start_monitoring()