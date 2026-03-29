import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================
TRAIN_FILE = '../docs/8/features_dataset_rul_8.csv'
TEST_FILE = '../docs/9/features_dataset_rul_9.csv'


def prepare_data(file_path):
    """Обрезает мертвую зону: оставляет только жизнь сервера + 30 сек после отказа"""
    df = pd.read_csv(file_path)
    failures = df[df['RUL_sec'] == 0]

    cutoff_idx = len(df)
    if not failures.empty:
        # Берем индекс первой секунды отказа и добавляем 30 секунд "дна"
        cutoff_idx = min(failures.index[0] + 30, len(df))

    df_active = df.iloc[:cutoff_idx].copy()

    X = df_active.drop(columns=['timestamp', 'RUL_sec'])
    y = df_active['RUL_sec']
    return X, y, df_active['timestamp']


def main():
    print("🧠 Запуск кросс-экспериментальной валидации ML-модели...")

    # 1. Загрузка и обрезка данных
    X_train, y_train, _ = prepare_data(TRAIN_FILE)
    X_test, y_test, test_timestamps = prepare_data(TEST_FILE)

    print(f"Обучающая выборка (Эксперимент 8): {len(X_train)} строк")
    print(f"Тестовая выборка (Эксперимент 9): {len(X_test)} строк")

    # 2. Обучение модели Random Forest
    print("\n⏳ Обучение модели...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 3. Прогнозирование на незнакомом датасете
    preds = model.predict(X_test)

    # 4. Метрики
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)

    print("\n📊 Результаты кросс-валидации (Метрики):")
    print(f"MAE (Средняя ошибка): {mae:.2f} секунд")
    print(f"RMSE: {rmse:.2f} секунд")
    print(f"R^2 Score: {r2:.4f}")

    # 5. Визуализация
    plt.figure(figsize=(12, 6))
    plt.plot(range(len(y_test)), y_test.values, label='Фактический RUL (Эксперимент 9)', color='blue', linewidth=2)
    plt.plot(range(len(preds)), preds, label='Прогноз модели (обучена на Эксп. 8)', color='red', linestyle='dashed',
             linewidth=2)

    plt.title('Прогнозирование деградации на независимом эксперименте (Cross-Validation)', fontsize=14)
    plt.xlabel('Время (Секунды)', fontsize=12)
    plt.ylabel('Остаточный ресурс (Секунды до отказа)', fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('cross_val_prediction.png')
    print("\n✅ Итоговый график сохранен как 'cross_val_prediction.png'")

    # 6. Важность признаков
    importances = model.feature_importances_
    fi_df = pd.DataFrame({'Feature': X_train.columns, 'Importance': importances})
    print("\n🏆 Топ-5 самых важных фичей, предсказавших отказ:")
    print(fi_df.sort_values(by='Importance', ascending=False).head(5).to_string(index=False))


if __name__ == "__main__":
    main()