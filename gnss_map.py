"""Интерактивная карта результатов контроля RTK-решений."""

from pathlib import Path  # Класс для работы с путями к файлам.
import plotly.express as px  # Библиотека для построения интерактивной карты.

CATEGORY_COLORS = {  # Цвета категорий на карте.
    "Принято без дополнительной проверки": "#2ca02c",
    "Требуется дополнительная проверка": "#ff7f0e",
    "В пределах допуска — принято": "#2ca02c",
    "В пределах допуска — требуется проверка": "#ff7f0e",
    "Превышение допуска — обнаружено": "#7f0000",
    "Превышение допуска — пропущено": "#d62728",
}


def save_quality_map(data, map_path):
    """Построить карту RTK-решений и сохранить её в HTML-файл."""
    plot_data = data.astype({"quality_category": "object"})  # Готовим категории для Plotly.
    hover_columns = ["output_time", "ratio", "n_sat_solution",  # Поля подсказки.
                     "pos_sigma_h", "pos_sigma_v", "risk_score"]
    if "fixed_error_h" in plot_data.columns:  # Проверяем наличие опорной ошибки.
        hover_columns.append("fixed_error_h")  # Показываем её в учебном режиме.

    figure = px.scatter_mapbox(  # Строим точки маршрута по строкам таблицы.
        plot_data, lat="fixed_lat_deg", lon="fixed_lon_deg",
        color="quality_category", color_discrete_map=CATEGORY_COLORS,
        hover_name="quality_category", hover_data=hover_columns,
        zoom=12, center={"lat": plot_data["fixed_lat_deg"].median(),
                         "lon": plot_data["fixed_lon_deg"].median()},
    )

    has_reference = {"reference_lat_deg", "reference_lon_deg"}.issubset(plot_data.columns)
    lat_column = "reference_lat_deg" if has_reference else "fixed_lat_deg"  # Широта линии.
    lon_column = "reference_lon_deg" if has_reference else "fixed_lon_deg"  # Долгота линии.
    line_name = "Опорная траектория" if has_reference else "Траектория RTK"  # Легенда.
    route = plot_data.sort_values("gps_seconds").iloc[::10]  # Прореживаем линию маршрута.
    figure.add_scattermapbox(  # Добавляем линию траектории.
        lat=route[lat_column], lon=route[lon_column], mode="lines",
        line={"color": "#252525", "width": 2}, name=line_name, hoverinfo="skip")

    figure.update_traces(marker={"size": 7, "opacity": 0.8}, selector={"mode": "markers"})
    figure.update_layout(  # Настраиваем карту и легенду.
        title="Вторичный контроль фиксированных RTK-решений",
        mapbox_style="carto-positron", height=700,
        margin={"l": 0, "r": 0, "t": 45, "b": 0},
        legend={"orientation": "h", "y": 0.01, "x": 0.01})

    map_path = Path(map_path)  # Преобразуем строку пути в объект Path.
    html = figure.to_html(include_plotlyjs=True, full_html=True)  # Встраиваем Plotly в HTML.
    map_path.write_text(html, encoding="utf-8")  # Сохраняем русские подписи в UTF-8.
