import pandas as pd
import numpy as np

# ==========================================
# КОНФИГУРАЦИЯ ЭКСПЕРИМЕНТА
# ==========================================
LOCUST_FILE = '../docs/7/experiment_7_stats_history.csv'
EVENT_LOOP_FILE = '../docs/7/event_loop_lag.csv'
DOCKER_FILE = '../docs/7/docker_metrics.csv'
OUTPUT_FILE = '../docs/7/master_dataset_rul.csv'

# Жесткий порог SLA для определения точки отказа
FAILURE_THRESHOLD_MS = 2000


# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================
def p95_agg(x):
    """Кастомная агрегация для вычисления 95-го перцентиля."""
    return x.quantile(0.95)


def parse_mem(mem_str):
    """Парсинг строки памяти Docker (например, '64.53MiB / 512MiB') в float (MiB)."""
    try:
        val = str(mem_str).split('/')[0].strip()
        if 'GiB' in val:
            return float(val.replace('GiB', '')) * 1024
        elif 'MiB' in val:
            return float(val.replace('MiB', ''))
        elif 'kB' in val:
            return float(val.replace('kB', '')) / 1024
        elif 'B' in val:
            return float(val.replace('B', '')) / (1024 * 1024)
        return float(''.join(filter(lambda x: x.isdigit() or x == '.', val)))
    except:
        return 0.0


# ==========================================
# ОСНОВНОЙ ПАЙПЛАЙН
# ==========================================
def main():
    print("🚀 Запуск пайплайна подготовки датасета...")

    # --- ШАГ 1: Обработка сырых метрик Event Loop ---
    print("1️⃣ Агрегация метрик Event Loop...")
    lag_df = pd.read_csv(EVENT_LOOP_FILE)
    lag_df['timestamp'] = pd.to_datetime(lag_df['timestamp'], unit='s').dt.floor('s')

    lag_agg = lag_df.groupby('timestamp').agg(
        requests_count=('event_loop_lag_sec', 'count'),
        lag_mean=('event_loop_lag_sec', 'mean'),
        lag_max=('event_loop_lag_sec', 'max'),
        lag_p95=('event_loop_lag_sec', p95_agg)
    ).reset_index()

    # --- ШАГ 2: Обработка метрик продуктивности (Locust) ---
    print("2️⃣ Обработка данных Locust...")
    locust_df = pd.read_csv(LOCUST_FILE)
    locust = locust_df[locust_df['Name'] == 'Aggregated'].copy()

    # Защита от отсутствия строки Aggregated
    if locust.empty:
        locust = locust_df.groupby('Timestamp').agg({
            'User Count': 'mean',
            'Requests/s': 'sum',
            'Failures/s': 'sum',
            '50%': 'mean',
            '95%': 'mean'
        }).reset_index()
    else:
        locust = locust[['Timestamp', 'User Count', 'Requests/s', 'Failures/s', '50%', '95%']]

    locust['timestamp'] = pd.to_datetime(locust['Timestamp'], unit='s')
    locust.drop(columns=['Timestamp'], inplace=True, errors='ignore')

    # --- ШАГ 3: Обработка аппаратных метрик (Docker) ---
    print("3️⃣ Очистка данных Docker...")
    docker = pd.read_csv(DOCKER_FILE, header=None, names=['ts', 'cpu_percent', 'mem_usage'])
    docker['cpu_percent'] = docker['cpu_percent'].str.replace('%', '').astype(float)
    docker['mem_mib'] = docker['mem_usage'].apply(parse_mem)
    docker['timestamp'] = pd.to_datetime(docker['ts'], unit='s')
    docker.drop(columns=['ts', 'mem_usage'], inplace=True)

    # --- ШАГ 4: Слияние (Merge & Interpolation) ---
    print("4️⃣ Слияние в единый Master Dataset...")
    master = pd.merge(locust, lag_agg, on='timestamp', how='outer')
    master = pd.merge(master, docker, on='timestamp', how='outer')

    master = master.sort_values('timestamp').reset_index(drop=True)

    # Интерполяция (Forward Fill) для Docker, так как он пишет раз в ~2.3 секунды
    master['cpu_percent'] = master['cpu_percent'].ffill()
    master['mem_mib'] = master['mem_mib'].ffill()
    master.fillna(0, inplace=True)  # Оставшиеся NaN заполняем нулями

    master.rename(columns={
        'User Count': 'users',
        'Requests/s': 'rps',
        'Failures/s': 'fails_ps',
        '50%': 'p50_response_ms',
        '95%': 'p95_response_ms',
    }, inplace=True)

    # --- ШАГ 5: Расчет целевой переменной RUL (Remaining Useful Life) ---
    print(f"5️⃣ Расчет остаточного ресурса (RUL). Порог: {FAILURE_THRESHOLD_MS} мс...")
    failures = master[master['p95_response_ms'] > FAILURE_THRESHOLD_MS]

    if not failures.empty:
        first_failure_time = failures['timestamp'].iloc[0]
        print(f"   ⚠️ Первый жесткий отказ зафиксирован в: {first_failure_time}")

        master['RUL_sec'] = (first_failure_time - master['timestamp']).dt.total_seconds()

        # Обнуляем RUL после отказа (система мертва)
        master.loc[master['RUL_sec'] < 0, 'RUL_sec'] = 0
    else:
        print("   ✅ Внимание: Система ни разу не превысила порог отказа.")
        # Если отказов не было, считаем, что ресурса хватило до конца теста
        last_time = master['timestamp'].iloc[-1]
        master['RUL_sec'] = (last_time - master['timestamp']).dt.total_seconds()

    # Сохранение результата
    master.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Готово! Датасет сохранен в '{OUTPUT_FILE}'. Строк: {len(master)}")


if __name__ == "__main__":
    main()