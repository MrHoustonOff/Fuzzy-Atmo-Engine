# Файл: src/fuzzy_engine/forecast_preprocessor.py
"""
Модуль предварительной обработки данных для прогнозной системы (Система Б).

Основная задача этого модуля - "свернуть" временные ряды (массивы)
почасовых данных в набор единичных статистических показателей.
Эти показатели затем используются в качестве входов для прогнозного
движка нечеткой логики.
"""
from datetime import datetime
import numpy as np
from src.utils.logger import console


def preprocess_hourly_data(
    hourly_data: dict,
    hours_to_forecast: int = 24
) -> dict:
    """
    Агрегирует почасовые данные о загрязнителях в ключевые статистики.

    Вычисляет средние и максимальные значения, количество часов с превышением
    порогов, а также ищет час пиковой нагрузки для PM2.5.

    Args:
        hourly_data (dict): Словарь, содержащий массивы почасовых данных
                            от API (например, 'time', 'pm2_5', 'no2').
        hours_to_forecast (int): Количество часов из начала массива,
                                 которые нужно учесть при расчетах.

    Returns:
        dict: Словарь с вычисленными статистическими показателями,
              готовый для подачи в `forecast_engine`. В случае ошибки
              возвращает пустой словарь.
    """
    if 'time' not in hourly_data or not hourly_data['time']:
        console.log("[bold red]Ошибка препроцессора: 'hourly' данные отсутствуют или пусты.[/]")
        return {}

    processed_inputs = {}

    try:
        # --- 1. Подготовка данных: срез на заданное количество часов ---
        num_available_hours = len(hourly_data['time'])
        slice_hours = min(num_available_hours, hours_to_forecast)

        # Безопасное извлечение и преобразование данных в numpy массивы
        def get_sliced_array(key: str) -> np.ndarray:
            # Если данных нет, возвращаем пустой массив, чтобы избежать ошибок
            return np.array(hourly_data.get(key, [])[:slice_hours], dtype=float)

        time_array = hourly_data['time'][:slice_hours]
        pm2_5_array = get_sliced_array('pm2_5')
        so2_array = get_sliced_array('sulphur_dioxide')
        no2_array = get_sliced_array('nitrogen_dioxide')
        co_array = get_sliced_array('carbon_monoxide')
        o3_array = get_sliced_array('ozone')

        # --- 2. Расчет статистик для PM2.5 (основной загрязнитель) ---
        if pm2_5_array.size > 0:
            processed_inputs['pm_avg'] = np.nanmean(pm2_5_array)
            processed_inputs['pm_max'] = np.nanmax(pm2_5_array)
            # Считаем количество часов, когда PM2.5 > 40 (условно "нездоровый" порог)
            processed_inputs['pm_hours_bad'] = np.sum(pm2_5_array > 40)

            # Определение часа пиковой концентрации PM2.5
            try:
                peak_index = np.nanargmax(pm2_5_array)
                peak_time_iso = time_array[peak_index]
                processed_inputs['pm_peak_hour'] = datetime.fromisoformat(peak_time_iso).hour
            except (ValueError, IndexError):
                processed_inputs['pm_peak_hour'] = -1  # В случае ошибки
        else:
            # Если данных по PM2.5 нет, заполняем нулями
            processed_inputs.update({'pm_avg': 0, 'pm_max': 0, 'pm_hours_bad': 0, 'pm_peak_hour': -1})

        # --- 3. Расчет нормализованного риска от газов ---
        # Концентрации нормализуются относительно их "опасных" порогов,
        # чтобы привести их к единой шкале. Берется максимальное значение.
        so2_norm = np.nanmean(so2_array) / 700 if so2_array.size > 0 else 0
        no2_norm = np.nanmean(no2_array) / 600 if no2_array.size > 0 else 0
        co_norm = np.nanmean(co_array) / 15000 if co_array.size > 0 else 0
        processed_inputs['gas_norm_risk'] = max(so2_norm, no2_norm, co_norm) * 100

        # --- 4. Расчет статистик для озона (O3) ---
        if o3_array.size > 0:
            processed_inputs['o3_max'] = np.nanmax(o3_array)
        else:
            processed_inputs['o3_max'] = 0

    except Exception:
        console.log(f"[bold red]Критическая ошибка в препроцессоре прогноза:[/]")
        console.print_exception()
        return {}

    return processed_inputs
