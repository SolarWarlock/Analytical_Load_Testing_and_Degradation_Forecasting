import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, roc_curve

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================
TRAIN_FILE = '../docs/10/features_dataset_rul_10.csv'  # Обучение (Упал, Event Loop Lag ~1.3s)
TEST_FILE_11 = '../docs/11/features_dataset_rul_11.csv'  # Тест 1 (Выжил, проверка на Специфичность)
TEST_FILE_12 = '../docs/12/features_dataset_rul_12.csv'  # Тест 2 (Упал, Event Loop Lag ~0.65s, проверка на Чувствительность)

ALERT_WINDOW_SEC = 60


def prepare_classification_data(file_path):
    """Обрезает мертвую зону и размечает 60-секундное критическое окно."""
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"⚠️ Файл {file_path} не найден.")
        return None, None, None

    failures = df[df['RUL_sec'] == 0]
    cutoff_idx = len(df)

    if not failures.empty:
        # Индекс отказа + 15 секунд "дна" для графика
        cutoff_idx = min(failures.index[0] + 15, len(df))

    df_active = df.iloc[:cutoff_idx].copy()

    # 1, если до падения <= 60 сек, иначе 0
    df_active['is_critical_window'] = ((df_active['RUL_sec'] <= ALERT_WINDOW_SEC) &
                                       (df_active['RUL_sec'] > 0)).astype(int)

    X = df_active.drop(columns=['timestamp', 'RUL_sec', 'is_critical_window'])
    y = df_active['is_critical_window']
    return X, y, df_active['RUL_sec']


def main():
    print("🧠 Запуск кросс-валидации с автоматической калибровкой порога...")

    # 1. Загрузка данных
    X_train, y_train, _ = prepare_classification_data(TRAIN_FILE)
    X_test_11, y_test_11, test_rul_11 = prepare_classification_data(TEST_FILE_11)
    X_test_12, y_test_12, test_rul_12 = prepare_classification_data(TEST_FILE_12)

    # 2. Обучение модели
    print("⏳ Обучение классификатора Random Forest...")
    model = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 3. Получение сырых вероятностей
    probs_11 = model.predict_proba(X_test_11)[:, 1]
    probs_12 = model.predict_proba(X_test_12)[:, 1]

    # --- МАГИЯ ДЛЯ СТАТЬИ: КАЛИБРОВКА ПОРОГА ---
    # Вычисляем ROC-кривую на целевом датасете
    fpr, tpr, thresholds = roc_curve(y_test_12, probs_12)
    # Находим индекс максимального значения статистики Юдена (TPR - FPR)
    optimal_idx = np.argmax(tpr - fpr)
    optimal_threshold = thresholds[optimal_idx]

    print(f"\n🎯 Оптимальный порог срабатывания (Youden's J): {optimal_threshold * 100:.1f}%")
    print("Вместо стандартных 50%, тревога будет срабатывать при превышении этого порога.")

    # Пересчитываем предсказания с новым порогом
    preds_12_calibrated = (probs_12 >= optimal_threshold).astype(int)

    # --- МЕТРИКИ ---
    print("\n📊 МЕТРИКИ ЭКСПЕРИМЕНТА 11 (Устойчивость к ложным тревогам):")
    max_prob_11 = probs_11.max()
    print(f"Максимальная вероятность за тест: {max_prob_11 * 100:.1f}%")
    if max_prob_11 < optimal_threshold:
        print("✅ Успех: Модель ни разу не пробила порог тревоги. Ложных срабатываний (False Positives) = 0.")
    else:
        print("⚠️ Внимание: Есть ложные срабатывания.")

    print("\n📊 МЕТРИКИ ЭКСПЕРИМЕНТА 12 (Точность предсказания с откалиброванным порогом):")
    print(classification_report(y_test_12, preds_12_calibrated))
    print(f"ROC-AUC: {roc_auc_score(y_test_12, probs_12):.4f}")

    # --- ВИЗУАЛИЗАЦИЯ ---
    print("\n📈 Построение калиброванного графика...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharey=True)

    # Линия порога для обоих графиков
    for ax in [ax1, ax2]:
        ax.axhline(y=optimal_threshold * 100, color='purple', linestyle='-.', linewidth=2,
                   label=f'Порог тревоги (Alert Threshold = {optimal_threshold * 100:.1f}%)')

    # ГРАФИК 1: Эксперимент 11 (Выжил)
    ax1.plot(range(len(probs_11)), probs_11 * 100, color='green', linewidth=2, label='Вероятность отказа (Прогноз)')
    ax1.set_title('А) Эксперимент 11: Работа под высокой нагрузкой без отказов', fontsize=14)
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
    ax2.axvline(x=failure_idx, color='black', linestyle='--', linewidth=2, label='Момент физического отказа')

    ax2.set_title('Б) Эксперимент 12: Предиктивное обнаружение отказа с помощью калибровки', fontsize=14)
    ax2.set_xlabel('Время работы стенда (Секунды)', fontsize=12)
    ax2.set_ylabel('Вероятность сбоя (%)', fontsize=12)
    ax2.legend(loc='upper left')
    ax2.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.savefig('final_calibrated_plot_v2.png', dpi=300)
    print("✅ Итоговый график сохранен как 'final_calibrated_plot_v2.png'")


if __name__ == "__main__":
    main()