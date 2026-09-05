"""Применение модели вторичного контроля фиксированных RTK-решений."""

from pathlib import Path  # Класс для работы с путями к файлам.
import joblib  # Библиотека для загрузки обученной модели.
import pandas as pd  # Библиотека для работы с таблицами.
from gnss_map import save_quality_map  # Функция сохранения интерактивной карты.

PROJECT_DIR = Path(__file__).resolve().parent  # Папка проекта.
DATA_FILE = PROJECT_DIR / "data" / "rtk_demo.csv"  # Входные RTK-данные.
MODEL_FILE = PROJECT_DIR / "models" / "lr4_rtk_quality_model.joblib"  # Модель LR-4.
RESULT_FILE = PROJECT_DIR / "results" / "rtk_checked.csv"  # Таблица результата.
MAP_FILE = PROJECT_DIR / "results" / "rtk_quality_map.html"  # Карта результата.


def analyze_gnss_data(data_file=DATA_FILE):
    """Загрузить данные, применить модель и сохранить результаты."""
    data = pd.read_csv(data_file)  # Загружаем подготовленные фиксированные решения.
    model_bundle = joblib.load(MODEL_FILE)  # Загружаем модель и её параметры.
    features = model_bundle["features"]  # Получаем признаки, использованные при обучении.
    missing_columns = [name for name in features if name not in data.columns]  # Ищем пропуски.
    if missing_columns:  # Останавливаем обработку при отсутствии признаков.
        raise ValueError(f"В данных отсутствуют признаки модели: {missing_columns}")

    model_data = data[features].apply(pd.to_numeric, errors="raise")  # Готовим вход модели.
    risk_score = model_bundle["model"].predict_proba(model_data)[:, 1]  # Рассчитываем риск.
    threshold = float(model_bundle["threshold"])  # Получаем порог классификации.
    tolerance = float(model_bundle["horizontal_tolerance_m"])  # Получаем допуск в метрах.
    result = data.copy()  # Сохраняем исходную таблицу без изменений.
    result["risk_score"] = risk_score  # Добавляем показатель классификационного риска.
    result["requires_review"] = risk_score > threshold  # Отмечаем подозрительные эпохи.
    result["quality_category"] = "Принято без дополнительной проверки"  # Базовая категория.
    result.loc[result["requires_review"], "quality_category"] = "Требуется дополнительная проверка"

    if "fixed_error_h" in result.columns:  # Используем опорную ошибку только для демонстрации.
        exceeds = pd.to_numeric(result["fixed_error_h"]) > tolerance  # Проверяем допуск.
        result["actual_exceeds_tolerance"] = exceeds  # Сохраняем фактическое превышение.
        result["quality_category"] = "В пределах допуска — принято"  # Базовая категория.
        result.loc[~exceeds & result["requires_review"], "quality_category"] = "В пределах допуска — требуется проверка"
        result.loc[exceeds & result["requires_review"], "quality_category"] = "Превышение допуска — обнаружено"
        result.loc[exceeds & ~result["requires_review"], "quality_category"] = "Превышение допуска — пропущено"

    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)  # Создаём папку результатов.
    result.to_csv(RESULT_FILE, index=False)  # Сохраняем таблицу классификации.
    save_quality_map(result, MAP_FILE)  # Сохраняем интерактивную карту.
    return result, model_bundle  # Возвращаем результат и параметры модели.


def main():
    """Запустить полный демонстрационный сценарий."""
    result, model_bundle = analyze_gnss_data()  # Выполняем весь цикл обработки.
    print(f"Признаки модели: {model_bundle['features']}")  # Показываем вход модели.
    print(f"Порог классификации: {model_bundle['threshold']:.4f}")  # Показываем порог.
    print(f"Горизонтальный допуск: {model_bundle['horizontal_tolerance_m']:.2f} м")
    print(f"Обработано эпох: {len(result)}")  # Показываем объём данных.
    print(result["quality_category"].value_counts().to_string())  # Показываем категории.
    print(f"Результат сохранён: {RESULT_FILE}")  # Показываем путь к таблице.
    print(f"Карта сохранена: {MAP_FILE}")  # Показываем путь к карте.


if __name__ == "__main__":  # Выполняем main только при прямом запуске файла.
    main()  # Запускаем приложение.