import pandas as pd

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================
INPUT_FILE = '../docs/10/master_dataset_rul.csv'
OUTPUT_FILE = '../docs/10/features_dataset_rul.csv'

# Базовые метрики, для которых мы будем искать исторические тренды
TARGET_FEATURES = ['cpu_percent', 'mem_mib', 'lag_p95', 'rps']

# Размеры скользящих окон в секундах
# 5 сек - быстрая реакция, 15 сек - средний тренд, 30 сек - долгосрочный накопительный эффект
WINDOW_SIZES = [5, 15, 30]


def main():
    print("🧠 Запуск генерации временных признаков (Feature Engineering)...")

    try:
        df = pd.read_csv(INPUT_FILE)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Убедимся, что данные отсортированы по времени
        df = df.sort_values('timestamp').reset_index(drop=True)

        print(f"Исходный размер датасета: {df.shape}")

        for feature in TARGET_FEATURES:
            for window in WINDOW_SIZES:
                # 1. Скользящее среднее (Moving Average) - сглаживает шум, показывает тренд
                df[f'{feature}_roll_mean_{window}s'] = df[feature].rolling(window=window, min_periods=1).mean()

                # 2. Скользящее стандартное отклонение (Rolling Std) - показывает волатильность/нестабильность
                df[f'{feature}_roll_std_{window}s'] = df[feature].rolling(window=window, min_periods=1).std()

                # 3. Градиент (Rate of Change) - насколько выросла/упала метрика по сравнению с X секунд назад
                # diff() дает разницу между текущим значением и значением X строк назад
                df[f'{feature}_diff_{window}s'] = df[feature].diff(periods=window)

        # Стандартное отклонение для окна из 1 элемента дает NaN, а diff() дает NaN для первых X строк.
        # Заполним эти пропуски обратным проходом (Backfill), чтобы не терять начало эксперимента.
        df.bfill(inplace=True)
        # Если в самом начале std всё ещё NaN (если значения одинаковые), заполним нулями
        df.fillna(0, inplace=True)

        df.to_csv(OUTPUT_FILE, index=False)

        print("\n✅ Генерация признаков завершена!")
        print(f"Новый размер датасета: {df.shape}")

        # Выведем список всех созданных фичей
        new_cols = [c for c in df.columns if 'roll' in c or 'diff' in c]
        print(f"\nСоздано {len(new_cols)} новых признаков. Примеры:")
        print(new_cols[:5])

    except FileNotFoundError:
        print(f"❌ Ошибка: Файл {INPUT_FILE} не найден. Сначала выполните prepare_dataset.py")
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")


if __name__ == "__main__":
    main()