# Файл: src/fuzzy_engine/forecast_system.py
"""
Модуль для "Прогнозного движка" нечеткой логики (Система Б).

Эта система принимает на вход агрегированные статистические данные
за 24-часовой период (например, среднее и максимальное значение PM2.5,
количество "плохих" часов, нормализованный риск от газов) и вычисляет
единый показатель 'Forecast_Risk' на предстоящие сутки.
"""
import numpy as np
import skfuzzy as fuzz
import skfuzzy.control as ctrl


def create_forecast_engine() -> ctrl.ControlSystem:
    """
    Создает, настраивает и возвращает "движок" для прогнозной системы.

    Внутри этой функции происходит полный цикл создания системы:
    1. Определение "Вселенных" (диапазонов) для входных и выходных данных.
    2. Создание переменных и их функций принадлежности.
    3. Определение базы правил.
    4. Сборка и возврат готовой системы управления.

    Returns:
        ctrl.ControlSystem: Готовая к использованию система прогнозирования.
    """
    # 1. Определение "Вселенных" (числовых диапазонов)
    universe_pm_avg = np.arange(0, 501, 1)      # Среднее PM2.5
    universe_pm_max = np.arange(0, 501, 1)      # Максимум PM2.5
    universe_pm_hours = np.arange(0, 25, 1)     # Кол-во часов с >40 PM2.5
    universe_gas_risk = np.arange(0, 101, 1)    # Нормализованный риск от газов
    universe_o3_max = np.arange(0, 1001, 1)     # Максимум O3
    universe_forecast_risk = np.arange(0, 101, 1)  # Выходной риск (0-100)

    # 2. Создание входных (Antecedent) и выходных (Consequent) переменных
    pm_avg = ctrl.Antecedent(universe_pm_avg, 'pm_avg')
    pm_max = ctrl.Antecedent(universe_pm_max, 'pm_max')
    pm_hours_bad = ctrl.Antecedent(universe_pm_hours, 'pm_hours_bad')
    gas_norm_risk = ctrl.Antecedent(universe_gas_risk, 'gas_norm_risk')
    o3_max = ctrl.Antecedent(universe_o3_max, 'o3_max')
    forecast_risk = ctrl.Consequent(universe_forecast_risk, 'Forecast_Risk')

    # 3. Определение функций принадлежности для входов
    pm_avg['low'] = fuzz.trapmf(pm_avg.universe, [0, 0, 10, 15])
    pm_avg['med'] = fuzz.trapmf(pm_avg.universe, [10, 15, 30, 40])
    pm_avg['high'] = fuzz.trapmf(pm_avg.universe, [30, 40, 500, 500])

    pm_max['low'] = fuzz.trapmf(pm_max.universe, [0, 0, 30, 45])
    pm_max['med'] = fuzz.trapmf(pm_max.universe, [30, 45, 100, 150])
    pm_max['high'] = fuzz.trapmf(pm_max.universe, [100, 150, 500, 500])

    pm_hours_bad['low'] = fuzz.trapmf(pm_hours_bad.universe, [0, 0, 1, 3])
    pm_hours_bad['med'] = fuzz.trapmf(pm_hours_bad.universe, [1, 3, 6, 10])
    pm_hours_bad['high'] = fuzz.trapmf(pm_hours_bad.universe, [6, 10, 24, 24])

    gas_norm_risk['low'] = fuzz.trapmf(gas_norm_risk.universe, [0, 0, 10, 20])
    gas_norm_risk['med'] = fuzz.trapmf(gas_norm_risk.universe, [10, 20, 50, 60])
    gas_norm_risk['high'] = fuzz.trapmf(gas_norm_risk.universe, [50, 60, 100, 100])

    o3_max['low'] = fuzz.trapmf(o3_max.universe, [0, 0, 80, 120])
    o3_max['med'] = fuzz.trapmf(o3_max.universe, [80, 120, 170, 190])
    o3_max['high'] = fuzz.trapmf(o3_max.universe, [170, 190, 1000, 1000])

    # 4. Определение функций принадлежности для выхода
    forecast_risk['low'] = fuzz.trimf(forecast_risk.universe, [0, 15, 30])
    forecast_risk['medium'] = fuzz.trimf(forecast_risk.universe, [25, 45, 65])
    forecast_risk['high'] = fuzz.trimf(forecast_risk.universe, [60, 75, 90])
    forecast_risk['critical'] = fuzz.trimf(forecast_risk.universe, [85, 95, 100])

    # 5. Создание базы правил
    # Правило 1: Критический риск. Если максимальное значение (пик) любого
    # из основных загрязнителей будет высоким, прогнозный риск - критический.
    rule1 = ctrl.Rule(
        pm_max['high'] | gas_norm_risk['high'] | o3_max['high'],
        forecast_risk['critical']
    )

    # Правило 2: Высокий риск. Если среднее значение PM или количество
    # "плохих" часов высоки.
    rule2 = ctrl.Rule(pm_avg['high'] | pm_hours_bad['high'], forecast_risk['high'])

    # Правило 3 и 4: Средний риск. Активируются, если пиковые или средние
    # значения находятся в умеренном диапазоне.
    rule3 = ctrl.Rule(
        pm_max['med'] | gas_norm_risk['med'] | o3_max['med'],
        forecast_risk['medium']
    )
    rule4 = ctrl.Rule(pm_hours_bad['med'] | pm_avg['med'], forecast_risk['medium'])

    # Правило 5: Низкий риск. Самое строгое правило, требующее,
    # чтобы все статистические показатели были на низком уровне.
    rule5 = ctrl.Rule(
        pm_avg['low'] & pm_max['low'] & pm_hours_bad['low'] &
        gas_norm_risk['low'] & o3_max['low'],
        forecast_risk['low']
    )

    # 6. Сборка системы управления
    rules = [rule1, rule2, rule3, rule4, rule5]
    forecast_engine = ctrl.ControlSystem(rules)

    return forecast_engine