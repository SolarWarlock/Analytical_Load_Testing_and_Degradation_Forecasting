import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

TRAIN_FILE = '../docs/8/features_dataset_rul_8.csv'
TEST_FILE = '../docs/9/features_dataset_rul_9.csv'

# Окно упреждения (за сколько секунд мы хотим получать тревогу)
ALERT_WINDOW_SEC = 60


def prepare_classification_data(file_path):
    df = pd.read_csv(file_path)
    failures = df[df['RUL_sec'] == 0]

    cutoff_idx = len(df)
    if not failures.empty:
        # Берем индекс отказа + 15 секунд "дна"
        cutoff_idx = min(failures.index[0] + 15, len(df))

    df_active = df.iloc[:cutoff_idx].copy()

    # СОЗДАЕМ НОВУЮ ЦЕЛЕВУЮ ПЕРЕМЕННУЮ: 1, если до падения <= 60 сек, иначе 0
    # Исключаем моменты, когда сервер уже мертв (RUL == 0) из "предвестников"
    df_active['is_critical_window'] = ((df_active['RUL_sec'] <= ALERT_WINDOW_SEC) &
                                       (df_active['RUL_sec'] > 0)).astype(int)

    X = df_active.drop(columns=['timestamp', 'RUL_sec', 'is_critical_window'])
    y = df_active['is_critical_window']
    return X, y, df_active['RUL_sec']


def main():
    print("🧠 Запуск классификатора: Прогнозирование отказа за 60 секунд...")

    # 1. Загрузка данных
    X_train, y_train, _ = prepare_classification_data(TRAIN_FILE)
    X_test, y_test, test_rul = prepare_classification_data(TEST_FILE)

    # 2. Обучение модели
    # Используем class_weight='balanced', так как "критическое окно" занимает малую часть датасета
    model = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 3. Прогнозирование вероятности (Probability of Failure)
    # predict_proba возвращает вероятности для классов [0, 1]. Нам нужен класс 1 (отказ).
    failure_probabilities = model.predict_proba(X_test)[:, 1]

    # 4. Метрики для статьи
    preds_binary = model.predict(X_test)
    print("\n📊 Отчет по классификации (Эксперимент 9):")
    print(classification_report(y_test, preds_binary))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, failure_probabilities):.4f}")

    # 5. Визуализация: "Радар Деградации"
    plt.figure(figsize=(12, 6))

    # Рисуем вероятность падения
    plt.plot(range(len(failure_probabilities)), failure_probabilities * 100,
             color='red', linewidth=2, label='Вероятность отказа (Прогноз ML), %')

    # Выделяем фактическую зону, когда оставалось 60 секунд
    critical_zone_mask = y_test == 1
    plt.fill_between(range(len(y_test)), 0, 100, where=critical_zone_mask,
                     color='orange', alpha=0.3, label='Фактическое окно 60 сек до отказа')

    # Отмечаем момент жесткого падения
    failure_idx = test_rul[test_rul == 0].index[0] if not test_rul[test_rul == 0].empty else len(test_rul)
    plt.axvline(x=failure_idx, color='black', linestyle='--', linewidth=2, label='Момент отказа (RUL=0)')

    plt.title('Предиктивный мониторинг: Вероятность отказа системы', fontsize=14)
    plt.xlabel('Время работы стенда (Секунды)', fontsize=12)
    plt.ylabel('Вероятность сбоя (%)', fontsize=12)
    plt.ylim(0, 105)
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig('failure_probability_plot.png')
    print("\n✅ Итоговый график сохранен как 'failure_probability_plot.png'")


if __name__ == "__main__":
    main()