# Файл: src/fuzzy_engine/forecast_system.py

import numpy as np
import skfuzzy as fuzz
import skfuzzy.control as ctrl

"""
(Система Б, Шаг 2, 3, 4)
"Прогнозный Движок"
"""

def create_forecast_engine():
    """
    Собирает "движок" для "Прогнозной" Системы.
    """
    
    # --- ШАГ 1+2: "ВСЕЛЕННАЯ" И "ГРАФИКИ" ---
    
    # Входы (статистика "свернутых" массивов)
    universe_pm_avg = np.arange(0, 501, 1)
    universe_pm_max = np.arange(0, 501, 1)
    universe_pm_hours = np.arange(0, 25, 1) # (0-24 часа)
    universe_gas_risk = np.arange(0, 101, 1) # (0-100%)
    universe_o3_avg = np.arange(0, 1001, 1)
    universe_o3_max = np.arange(0, 1001, 1)

    # Выход (Прогнозный Риск, 0-100)
    universe_forecast_risk = np.arange(0, 101, 1)

    # Переменные Входа (Antecedents)
    pm_avg = ctrl.Antecedent(universe_pm_avg, 'pm_avg')
    pm_max = ctrl.Antecedent(universe_pm_max, 'pm_max')
    pm_hours_bad = ctrl.Antecedent(universe_pm_hours, 'pm_hours_bad')
    gas_norm_risk = ctrl.Antecedent(universe_gas_risk, 'gas_norm_risk')
    o3_max = ctrl.Antecedent(universe_o3_max, 'o3_max')
    
    # Переменная Выхода (Consequent)
    forecast_risk = ctrl.Consequent(universe_forecast_risk, 'Forecast_Risk')

    # "Графики" Входов
    pm_avg['low'] = fuzz.trapmf(pm_avg.universe, [0, 0, 10, 15])
    pm_avg['med'] = fuzz.trapmf(pm_avg.universe, [10, 15, 30, 40])
    pm_avg['high'] = fuzz.trapmf(pm_avg.universe, [30, 40, 500, 500])
    
    pm_max['low'] = fuzz.trapmf(pm_max.universe, [0, 0, 30, 45])
    pm_max['med'] = fuzz.trapmf(pm_max.universe, [30, 45, 100, 150])
    pm_max['high'] = fuzz.trapmf(pm_max.universe, [100, 150, 500, 500])

    pm_hours_bad['low'] = fuzz.trapmf(pm_hours_bad.universe, [0, 0, 1, 3]) # 0-3 часа
    pm_hours_bad['med'] = fuzz.trapmf(pm_hours_bad.universe, [1, 3, 6, 10]) # 3-10 часов
    pm_hours_bad['high'] = fuzz.trapmf(pm_hours_bad.universe, [6, 10, 24, 24]) # > 6 часов

    gas_norm_risk['low'] = fuzz.trapmf(gas_norm_risk.universe, [0, 0, 10, 20])
    gas_norm_risk['med'] = fuzz.trapmf(gas_norm_risk.universe, [10, 20, 50, 60])
    gas_norm_risk['high'] = fuzz.trapmf(gas_norm_risk.universe, [50, 60, 100, 100])
    
    o3_max['low'] = fuzz.trapmf(o3_max.universe, [0, 0, 80, 120])
    o3_max['med'] = fuzz.trapmf(o3_max.universe, [80, 120, 170, 190])
    o3_max['high'] = fuzz.trapmf(o3_max.universe, [170, 190, 1000, 1000])

    # "Графики" Выхода
    forecast_risk['low'] = fuzz.trimf(forecast_risk.universe, [0, 15, 30])
    forecast_risk['medium'] = fuzz.trimf(forecast_risk.universe, [25, 45, 65])
    forecast_risk['high'] = fuzz.trimf(forecast_risk.universe, [60, 75, 90])
    forecast_risk['critical'] = fuzz.trimf(forecast_risk.universe, [85, 95, 100])
    
    # --- ШАГ 3: "БАЗА ПРАВИЛ" (Прогноз) ---
    # Мы не будем мелочиться (как ты просил)
    
    # "Критические" правила (если ХОТЯ БЫ ОДИН "пик" - высокий)
    rule1 = ctrl.Rule(pm_max['high'] | gas_norm_risk['high'] | o3_max['high'], 
                      forecast_risk['critical'])
    
    # "Плохие" правила (если "среднее" - высокое)
    rule2 = ctrl.Rule(pm_avg['high'] | (pm_hours_bad['high']), 
                      forecast_risk['high'])
    
    # "Средние" правила (если "пики" - средние)
    rule3 = ctrl.Rule(pm_max['med'] | gas_norm_risk['med'] | o3_max['med'], 
                      forecast_risk['medium'])
    
    # "Средние" правила (если "часы" - средние)
    rule4 = ctrl.Rule(pm_hours_bad['med'] | pm_avg['med'],
                      forecast_risk['medium'])

    # "Хорошие" правила (если ВСЕ - низкое)
    rule5 = ctrl.Rule(
        pm_avg['low'] & pm_max['low'] & pm_hours_bad['low'] & 
        gas_norm_risk['low'] & o3_max['low'],
        forecast_risk['low']
    )
    
    rules = [rule1, rule2, rule3, rule4, rule5]
    
    # --- ШАГ 4: "СБОРКА" ---
    forecast_engine = ctrl.ControlSystem(rules)
    
    return forecast_engine