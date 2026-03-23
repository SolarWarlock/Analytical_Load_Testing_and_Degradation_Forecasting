import pandas as pd
import re


def clean_docker_metrics(input_filepath, output_filepath):
    # Регулярное выражение для отлова ANSI-последовательностей (цвета, очистка экрана и т.д.)
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

    clean_data = []

    # Открываем файл как сырой текст, так как мусор ломает стандартный CSV-парсер
    with open(input_filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Вырезаем терминальный мусор
            clean_line = ansi_escape.sub('', line).strip()

            if not clean_line:
                continue

            # После очистки строка выглядит так: "0.13%,32.93MiB / 512MiB"
            try:
                # Разбиваем по первой запятой
                cpu_part, mem_part = clean_line.split(',', 1)

                # Вытаскиваем только числовое значение CPU
                cpu_val = float(re.sub(r'[^\d.]', '', cpu_part))

                # Берем только левую часть памяти (до слэша / 512MiB)
                mem_current = mem_part.split('/')[0]
                mem_val = float(re.sub(r'[^\d.]', '', mem_current))

                clean_data.append({
                    'cpu_percent': cpu_val,
                    'memory_mib': mem_val
                })
            except ValueError:
                # Если строка совсем битая (например, заголовок или сбой записи), пропускаем её
                continue

    # Конвертируем в удобный DataFrame
    df = pd.DataFrame(clean_data)

    # Сохраняем чистый датасет
    df.to_csv(output_filepath, index=False)
    print(f"Очищено строк: {len(df)}")
    return df


# Запускаем очистку
df_clean = clean_docker_metrics('raw_data/docker_metrics.csv', 'raw_data/clean_docker_metrics.csv')
print(df_clean.head())