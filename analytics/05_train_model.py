import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================
INPUT_FILE = '../docs/9/features_dataset_rul_9.csv'


def main():
    print("🤖 Запуск машинного обучения (Predictive Maintenance)...")

    # 1. Загрузка данных
    df = pd.read_csv(INPUT_FILE)

    # Отделяем целевую переменную (y) и признаки (X)
    # Удаляем timestamp, так как алгоритм не понимает формат даты,
    # и удаляем RUL_sec, так как это то, что мы пытаемся предсказать.
    X = df.drop(columns=['timestamp', 'RUL_sec'])
    y = df['RUL_sec']

    # 2. Хронологическое разделение (Time-Series Split)
    # ВАЖНО для ВАК-статьи: мы не перемешиваем данные!
    # Мы берем первые 80% времени на обучение, а последние 20% (где происходит падение) - на тест.
    split_index = int(len(df) * 0.8)

    X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
    y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]
    test_timestamps = df['timestamp'].iloc[split_index:]

    print(f"Обучающая выборка (Train): {X_train.shape[0]} строк")
    print(f"Тестовая выборка (Test): {X_test.shape[0]} строк")

    # 3. Инициализация и обучение модели
    print("⏳ Обучение модели Random Forest...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 4. Прогнозирование на тестовой выборке
    predictions = model.predict(X_test)

    # 5. Оценка качества модели (Метрики для статьи)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    print("\n📊 Результаты прогнозирования (Метрики):")
    print(f"MAE (Средняя абсолютная ошибка): {mae:.2f} секунд")
    print(f"RMSE (Корень среднеквадратичной ошибки): {rmse:.2f} секунд")
    print(f"R^2 Score (Коэффициент детерминации): {r2:.4f}")
    print("Интерпретация MAE: в среднем модель ошибается в прогнозе времени до отказа на {:.2f} сек.".format(mae))

    # 6. Анализ важности признаков (Feature Importance)
    # Это покажет, какие метрики сильнее всего сигнализировали о скором падении
    importances = model.feature_importances_
    feature_names = X.columns
    fi_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
    fi_df = fi_df.sort_values(by='Importance', ascending=False).head(10)  # Топ-10 метрик

    print("\n🏆 Топ-10 самых важных метрик для предсказания деградации:")
    print(fi_df.to_string(index=False))

    # 7. Визуализация результата (Идеально для вставки в статью)
    print("\n📈 Построение графика...")
    plt.figure(figsize=(12, 6))
    plt.plot(range(len(y_test)), y_test.values, label='Фактический RUL (Реальность)', color='blue', linewidth=2)
    plt.plot(range(len(predictions)), predictions, label='Прогноз модели', color='red', linestyle='dashed', linewidth=2)

    plt.title('Прогнозирование времени до деградации (Test Split)', fontsize=14)
    plt.xlabel('Время (Секунды тестовой выборки)', fontsize=12)
    plt.ylabel('Остаточный ресурс (Секунды до отказа)', fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('../docs/9/rul_prediction_plot.png')
    print("✅ График сохранен как '../docs/9/rul_prediction_plot.png'")


if __name__ == "__main__":
    main()