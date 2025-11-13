# Файл: src/fuzzy_engine/forecast_preprocessor.py
# (ВЕРСИЯ 2.0 - "Прокачанная", ищет "час пика")

import numpy as np
from src.utils.logger import console
from datetime import datetime # <-- НУЖЕН ДЛЯ "ПАРСИНГА" ЧАСА

"""
(Система Б, Шаг 1)
"Мясокомбинат" Статистики.
"Сворачивает" 'hourly' массивы.
"""

def preprocess_hourly_data(hourly_data: dict, hours_to_forecast: int = 24) -> dict:
    """
    "Сворачивает" 'hourly' массивы.
    Возвращает dict с "агрегированными" входами.
    """
    
    processed_inputs = {}
    
    if 'time' not in hourly_data:
        console.log("[bold red]Ошибка Пре-процессора: 'hourly' данные отсутствуют.[/]")
        return processed_inputs

    try:
        # --- 1. Ограничиваем прогноз (срез на 24 часа) ---
        num_hours = len(hourly_data['time'])
        slice_hours = min(num_hours, hours_to_forecast)
        
        # "Режем" массивы
        time_array = hourly_data['time'][:slice_hours]
        pm2_5_array = np.array(hourly_data['pm2_5'][:slice_hours]).astype(float)
        pm10_array  = np.array(hourly_data['pm10'][:slice_hours]).astype(float)
        so2_array   = np.array(hourly_data['sulphur_dioxide'][:slice_hours]).astype(float)
        no2_array   = np.array(hourly_data['nitrogen_dioxide'][:slice_hours]).astype(float)
        co_array    = np.array(hourly_data['carbon_monoxide'][:slice_hours]).astype(float)
        o3_array    = np.array(hourly_data['ozone'][:slice_hours]).astype(float)
        

        # --- 2. "Матан": Считаем "статистики" ---
        
        # "Реактор 1: Частицы" (PM2.5)
        processed_inputs['pm_avg'] = np.nanmean(pm2_5_array)
        processed_inputs['pm_max'] = np.nanmax(pm2_5_array)
        processed_inputs['pm_hours_bad'] = np.sum(pm2_5_array > 40) # (Порог 'unhealthy')
        
        # --- "СЕКСИ МАТАН": ИЩЕМ "ЧАС ПИКА" PM2.5 ---
        try:
            pm_max_index = np.nanargmax(pm2_5_array)
            peak_time_iso = time_array[pm_max_index]
            # "Парсим" ISO-строку (напр., "2025-11-10T18:00") и "вытаскиваем" час (18)
            processed_inputs['pm_peak_hour'] = datetime.fromisoformat(peak_time_iso).hour
        except Exception:
            processed_inputs['pm_peak_hour'] = -1 # (Ошибка, если массив пуст)
        # -------------------------------------------

        # "Реактор 2: Газы" (Нормализованный риск)
        so2_norm = np.nanmean(so2_array) / 700 
        no2_norm = np.nanmean(no2_array) / 600
        co_norm  = np.nanmean(co_array) / 15000
        processed_inputs['gas_norm_risk'] = max(so2_norm, no2_norm, co_norm) * 100 

        # "Реактор 3: Озон" (O3)
        processed_inputs['o3_avg'] = np.nanmean(o3_array)
        processed_inputs['o3_max'] = np.nanmax(o3_array)
        # (Мы могли бы искать "час пика" и для O3, но PM2.5 - "главный" киллер)

    except Exception as e:
        console.log(f"[bold red]Ошибка Пре-процессора: Не удалось 'свернуть' массивы.[/]")
        console.print_exception()
        return {}

    return processed_inputs