import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

# ==========================================
# КОНФИГУРАЦИЯ (Три эксперимента для статьи)
# ==========================================
TRAIN_FILE = 'features_dataset_rul_10.csv'  # Обучение (Упал из-за Event Loop)
TEST_FILE_11 = 'features_dataset_rul_11.csv'  # Тест 1 (Выжил, проверка на False Positives)
TEST_FILE_12 = 'features_dataset_rul_12.csv'  # Тест 2 (Упадет из-за тяжелой нагрузки, проверка на True Positives)

# Окно упреждения (за сколько секунд мы хотим получать тревогу)
ALERT_WINDOW_SEC = 60


def prepare_classification_data(file_path):
    """Обрезает мертвую зону и размечает 60-секундное критическое окно."""
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"⚠️ Файл {file_path} еще не создан. Пропускаем...")
        return None, None, None

    failures = df[df['RUL_sec'] == 0]

    cutoff_idx = len(df)
    if not failures.empty:
        # Берем индекс отказа + 15 секунд "дна" для наглядности графика
        cutoff_idx = min(failures.index[0] + 15, len(df))

    df_active = df.iloc[:cutoff_idx].copy()

    # 1, если до падения <= 60 сек, иначе 0
    df_active['is_critical_window'] = ((df_active['RUL_sec'] <= ALERT_WINDOW_SEC) &
                                       (df_active['RUL_sec'] > 0)).astype(int)

    X = df_active.drop(columns=['timestamp', 'RUL_sec', 'is_critical_window'])
    y = df_active['is_critical_window']
    return X, y, df_active['RUL_sec']


def main():
    print("🧠 Запуск комплексной кросс-валидации (Обучение на Эксп. 10)...")

    # 1. Загрузка данных
    X_train, y_train, _ = prepare_classification_data(TRAIN_FILE)
    X_test_11, y_test_11, test_rul_11 = prepare_classification_data(TEST_FILE_11)
    X_test_12, y_test_12, test_rul_12 = prepare_classification_data(TEST_FILE_12)

    if X_train is None or X_test_12 is None:
        print("❌ Ошибка: Для полной картины нужны все три датасета (10, 11 и 12).")
        return

    # 2. Обучение модели
    print("⏳ Обучение классификатора Random Forest...")
    model = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 3. Прогнозирование на обоих тестовых наборах
    probs_11 = model.predict_proba(X_test_11)[:, 1]
    probs_12 = model.predict_proba(X_test_12)[:, 1]

    # --- МЕТРИКИ ДЛЯ СТАТЬИ ---
    print("\n📊 МЕТРИКИ ЭКСПЕРИМЕНТА 11 (Проверка на ложные тревоги / Specificity):")
    print(f"Максимальная вероятность отказа за весь тест: {probs_11.max() * 100:.1f}%")
    if len(np.unique(y_test_11)) > 1:
        print(f"ROC-AUC: {roc_auc_score(y_test_11, probs_11):.4f}")
    else:
        print("ROC-AUC не применим, так как в тесте 11 не было реальных отказов (идеальный True Negative).")

    print("\n📊 МЕТРИКИ ЭКСПЕРИМЕНТА 12 (Проверка на точное предсказание / Recall):")
    preds_12 = model.predict(X_test_12)
    print(classification_report(y_test_12, preds_12))
    print(f"ROC-AUC: {roc_auc_score(y_test_12, probs_12):.4f}")

    # --- ВИЗУАЛИЗАЦИЯ (СДВОЕННЫЙ ГРАФИК) ---
    print("\n📈 Построение графика для публикации...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharey=True)

    # ГРАФИК 1: Эксперимент 11 (Выжил)
    ax1.plot(range(len(probs_11)), probs_11 * 100, color='green', linewidth=2, label='Вероятность отказа (Прогноз)')
    ax1.set_title('А) Эксперимент 11: Устойчивость к ложным тревогам (Специфичность)', fontsize=14)
    ax1.set_ylabel('Вероятность сбоя (%)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, linestyle=':', alpha=0.6)

    # ГРАФИК 2: Эксперимент 12 (Упал)
    ax2.plot(range(len(probs_12)), probs_12 * 100, color='red', linewidth=2, label='Вероятность отказа (Прогноз)')

    # Оранжевая зона 60 секунд
    critical_zone_mask = y_test_12 == 1
    ax2.fill_between(range(len(y_test_12)), 0, 100, where=critical_zone_mask,
                     color='orange', alpha=0.3, label='Фактическое окно 60 сек до отказа')

    # Черная линия падения
    failure_idx = test_rul_12[test_rul_12 == 0].index[0] if not test_rul_12[test_rul_12 == 0].empty else len(
        test_rul_12)
    ax2.axvline(x=failure_idx, color='black', linestyle='--', linewidth=2, label='Момент отказа (RUL=0)')

    ax2.set_title('Б) Эксперимент 12: Предиктивное обнаружение отказа (Чувствительность)', fontsize=14)
    ax2.set_xlabel('Время работы стенда (Секунды)', fontsize=12)
    ax2.set_ylabel('Вероятность сбоя (%)', fontsize=12)
    ax2.legend(loc='upper left')
    ax2.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.savefig('final_paper_validation_plot.png', dpi=300)  # dpi=300 для высокого качества в статье
    print("✅ Итоговый график сохранен как 'final_paper_validation_plot.png'")


if __name__ == "__main__":
    main()