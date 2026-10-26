import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================
INPUT_FILE = '../docs/12/features_dataset_rul_12.csv'
OUTPUT_IMAGE = 'figure_4_raw_metrics.png'


def main():
    print(f"📊 Генерация графика сырых метрик из файла {INPUT_FILE}...")

    # 1. Загрузка данных
    df = pd.read_csv(INPUT_FILE)

    # 2. Поиск момента отказа (RUL = 0)
    failures = df[df['RUL_sec'] == 0]
    failure_idx = failures.index[0] if not failures.empty else len(df)

    # Отрезаем данные: берем активную фазу + 30 секунд после падения, чтобы было видно "дно"
    plot_end = min(failure_idx + 30, len(df))
    df_plot = df.iloc[:plot_end].copy()

    # Создаем шкалу времени в минутах для лучшей читаемости
    time_mins = np.arange(len(df_plot)) / 60.0
    failure_time_min = failure_idx / 60.0

    # 3. Настройка холста (3 графика друг под другом)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    # --- График 1: CPU ---
    ax1.plot(time_mins, df_plot['cpu_percent'], color='tab:blue', linewidth=1.5, alpha=0.8)
    ax1.set_ylabel('Утилизация CPU (%)', fontsize=11)
    ax1.set_title('Рис. 4. Динамика потребления ресурсов и задержки перед каскадным отказом', fontsize=13, pad=15)
    ax1.grid(True, linestyle=':', alpha=0.7)
    ax1.axvline(x=failure_time_min, color='black', linestyle='--', linewidth=2)

    # --- График 2: Оперативная память ---
    ax2.plot(time_mins, df_plot['mem_mib'], color='tab:purple', linewidth=2)
    ax2.set_ylabel('Потребление RAM (MiB)', fontsize=11)
    ax2.grid(True, linestyle=':', alpha=0.7)
    ax2.axvline(x=failure_time_min, color='black', linestyle='--', linewidth=2)

    # --- График 3: Задержка p95 (Сам отказ) ---
    ax3.plot(time_mins, df_plot['p95_response_ms'], color='tab:red', linewidth=2)
    ax3.set_ylabel('Задержка p95 (мс)', fontsize=11)
    ax3.set_xlabel('Время эксперимента (Минуты)', fontsize=12)
    ax3.grid(True, linestyle=':', alpha=0.7)

    # Добавляем линию отказа с подписью на нижний график
    ax3.axvline(x=failure_time_min, color='black', linestyle='--', linewidth=2, label='Момент физического отказа')
    ax3.legend(loc='upper left', fontsize=10)

    # 4. Сохранение
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=300)
    print(f"✅ График успешно сохранен как '{OUTPUT_IMAGE}'")


if __name__ == "__main__":
    main()