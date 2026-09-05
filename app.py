"""Веб-интерфейс для контроля фиксированных RTK-решений."""  # Назначение модуля.

from pathlib import Path  # Класс для работы с файловыми путями.

import streamlit as st  # Библиотека для создания веб-интерфейса.
from streamlit.components.v1 import html as show_html  # Компонент для показа готовой HTML-карты.

from gnss_backend import DATA_FILE, MAP_FILE, RESULT_FILE, analyze_gnss_data  # Функции и пути бэкенда.


PROJECT_DIR = Path(__file__).resolve().parent  # Папка проекта.
UPLOADED_FILE = PROJECT_DIR / "data" / "uploaded_input.csv"  # Временный файл пользователя.


st.set_page_config(page_title="GeoAI: контроль RTK", layout="centered")  # Настройки страницы.
st.title("GeoAI: контроль качества RTK-решений")  # Главный заголовок.
st.write("Модель находит фиксированные решения, которые требуют дополнительной проверки.")  # Краткое описание задачи.

uploaded_data = st.file_uploader("CSV-файл с результатами измерений", type="csv")  # Выбор файла на компьютере.

if uploaded_data is None:  # Сценарий без пользовательского файла.
    input_file = DATA_FILE  # Демонстрационный набор из папки проекта.
    st.caption(f"Используется демонстрационный файл: {DATA_FILE.name}")  # Имя текущего набора.
else:  # Сценарий с пользовательским файлом.
    UPLOADED_FILE.write_bytes(uploaded_data.getvalue())  # Сохранение загруженного CSV-файла.
    input_file = UPLOADED_FILE  # Путь к выбранному набору.
    st.caption(f"Выбран файл: {uploaded_data.name}")  # Имя пользовательского набора.

if st.button("Проверить RTK-решения", type="primary", use_container_width=True):  # Запуск обработки по запросу пользователя.
    try:  # Перехват ошибок чтения данных и применения модели.
        with st.spinner("Модель анализирует измерения..."):  # Индикатор выполнения расчета.
            result, model_bundle = analyze_gnss_data(input_file)  # Обработка выбранного файла.
        st.session_state["gnss_result"] = result  # Результат для повторных перерисовок страницы.
        st.session_state["model_bundle"] = model_bundle  # Параметры модели для блока итогов.
    except Exception as error:  # Любая ошибка пользовательского сценария.
        st.error(f"Не удалось обработать файл: {error}")  # Понятное сообщение в интерфейсе.

if "gnss_result" in st.session_state:  # Наличие успешно рассчитанного результата.
    result = st.session_state["gnss_result"]  # Итоговая таблица текущего запуска.
    model_bundle = st.session_state["model_bundle"]  # Параметры примененной модели.
    review_count = int(result["requires_review"].sum())  # Число эпох для дополнительной проверки.
    without_review_count = len(result) - review_count  # Число эпох без дополнительной проверки.

    st.success("Проверка завершена. Таблица и интерактивная карта сохранены.")  # Сообщение об успешном результате.
    metric_columns = st.columns(3)  # Три показателя в одной строке.
    metric_columns[0].metric("Всего эпох", f"{len(result):,}".replace(",", " "))  # Объем набора.
    metric_columns[1].metric("Без проверки", f"{without_review_count:,}".replace(",", " "))  # Обычные решения.
    metric_columns[2].metric("Проверить", f"{review_count:,}".replace(",", " "))  # Потенциально проблемные решения.
    st.caption(  # Основные параметры принятия решения.
        f"Порог модели: {float(model_bundle['threshold']):.4f}. "  # Значение порога классификации.
        f"Горизонтальный допуск учебного набора: {float(model_bundle['horizontal_tolerance_m']):.2f} м."  # Значение допуска.
    )

    st.subheader("Распределение результатов")  # Заголовок сводной таблицы.
    category_counts = result["quality_category"].value_counts().rename_axis("Категория").reset_index(name="Количество")  # Число эпох каждой категории.
    st.dataframe(category_counts, hide_index=True, use_container_width=True)  # Отображение сводной таблицы.

    st.subheader("Карта контроля")  # Заголовок картографического результата.
    show_html(MAP_FILE.read_text(encoding="utf-8"), height=720, scrolling=False)  # Интерактивная HTML-карта.

    with st.expander("Таблица с результатами"):  # Свернутый блок подробных данных.
        st.dataframe(result, hide_index=True, use_container_width=True)  # Все исходные и расчетные поля.

    download_columns = st.columns(2)  # Две кнопки выгрузки в одной строке.
    
    download_columns[0].download_button(  # Выгрузка итоговой таблицы.
        "Скачать CSV",  # Текст кнопки.
        data=RESULT_FILE.read_bytes(),  # Содержимое CSV-файла.
        file_name=RESULT_FILE.name,  # Имя скачиваемого файла.
        mime="text/csv",  # Тип содержимого.
        use_container_width=True,  # Ширина кнопки по размеру колонки.
    )

    download_columns[1].download_button(  # Выгрузка интерактивной карты.
        "Скачать карту HTML",  # Текст кнопки.
        data=MAP_FILE.read_bytes(),  # Содержимое HTML-файла.
        file_name=MAP_FILE.name,  # Имя скачиваемого файла.
        mime="text/html",  # Тип содержимого.
        use_container_width=True,  # Ширина кнопки по размеру колонки.
    )