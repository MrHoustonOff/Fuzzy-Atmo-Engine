# Файл: src/fuzzy_engine/membership_functions.py

import numpy as np
import skfuzzy as fuzz
import skfuzzy.control as ctrl

"""
Определение всех функций принадлежности.
Такая структура для будущей отчетности.

графики основываются на реальных индесах EPA (Агентства по охране окружающей среды США)
"""

def define_particle_variables():
    """
    Определяет Диапазоны и Функции принадлежности.
    Возвращает 4 входа (Antecedents) и 1 выход (Consequent).
    """

    # --- ШАГ 1: ОПРЕДЕЛЯЕМ ДИАПАЗОНЫ ---
    # Мы используем np.arange(старт, стоп, шаг)
    # Диапазоны взяты из стандартов AQI
    universe_pm2_5 = np.arange(0, 501, 1)  # 0-500 μg/m³
    universe_pm10  = np.arange(0, 601, 1)  # 0-600 μg/m³
    universe_aod   = np.arange(0, 5.1, 0.1)  # 0-5 (Aerosol Optical Depth)
    universe_dust  = np.arange(0, 1001, 1)  # 0-1000 μg/m³ (аналогично PM10)
    universe_risk  = np.arange(0, 101, 1)  # Наш выход (0-100)

    # --- ШАГ 2: ФУНКЦИИ ПРИНАДЛЕЖНОСТИ ---

    # 1. ВХОД: PM2.5 (Самый опасный)
    pm2_5 = ctrl.Antecedent(universe_pm2_5, 'pm2_5')
    pm2_5['good']     = fuzz.trapmf(pm2_5.universe, [0, 0, 10, 15])      # 0-15
    pm2_5['moderate'] = fuzz.trapmf(pm2_5.universe, [10, 15, 30, 40])    # 10-40
    pm2_5['unhealthy'] = fuzz.trapmf(pm2_5.universe, [30, 40, 140, 160]) # 30-160
    pm2_5['hazardous'] = fuzz.trapmf(pm2_5.universe, [140, 160, 500, 500]) # 140+

    # 2. ВХОД: PM10
    pm10 = ctrl.Antecedent(universe_pm10, 'pm10')
    pm10['good']     = fuzz.trapmf(pm10.universe, [0, 0, 40, 60])        # 0-60
    pm10['moderate'] = fuzz.trapmf(pm10.universe, [40, 60, 140, 170])    # 40-170
    pm10['unhealthy'] = fuzz.trapmf(pm10.universe, [140, 170, 340, 360]) # 140-360
    pm10['hazardous'] = fuzz.trapmf(pm10.universe, [340, 360, 600, 600]) # 340+

    # 3. ВХОД: AOD (Мутность)
    aod = ctrl.Antecedent(universe_aod, 'aod')
    aod['low']    = fuzz.trapmf(aod.universe, [0, 0, 0.5, 1])      # 0-1
    aod['medium'] = fuzz.trapmf(aod.universe, [0.5, 1, 2, 3])      # 0.5-3
    aod['high']   = fuzz.trapmf(aod.universe, [2, 3, 5, 5])        # 2+

    # 4. ВХОД: Dust (Пыль)
    dust = ctrl.Antecedent(universe_dust, 'dust')
    dust['low']    = fuzz.trapmf(dust.universe, [0, 0, 50, 150])
    dust['medium'] = fuzz.trapmf(dust.universe, [50, 150, 300, 450])
    dust['high']   = fuzz.trapmf(dust.universe, [300, 450, 1000, 1000])

    # 5. ВЫХОД: Particle_Risk (Риск от частиц)
    particle_risk = ctrl.Consequent(universe_risk, 'Particle_Risk')
    particle_risk['low']      = fuzz.trapmf(particle_risk.universe, [0, 0, 15, 30])
    particle_risk['medium']   = fuzz.trapmf(particle_risk.universe, [15, 30, 45, 60])
    particle_risk['high']     = fuzz.trapmf(particle_risk.universe, [45, 60, 75, 90])
    particle_risk['critical'] = fuzz.trapmf(particle_risk.universe, [75, 90, 100, 100])

    return [pm2_5, pm10, aod, dust], particle_risk


def define_gas_variables():
    """
    Определяет "Вселенную" и "Графики" для Под-системы "Газы".
    Возвращает 3 входа (Antecedents) и 1 выход (Consequent).
    """
    
    # --- ШАГ 1: ОПРЕДЕЛЯЕМ "ВСЕЛЕННУЮ" (ДИАПАЗОНЫ) ---
    # Диапазоны μg/m³ взяты из стандартов AQI
    universe_co   = np.arange(0, 50001, 10)  # 0-50,000 μg/m³ (CO очень "тяжелый")
    universe_no2  = np.arange(0, 2001, 1)   # 0-2,000 μg/m³
    universe_so2  = np.arange(0, 2001, 1)   # 0-2,000 μg/m³
    
    universe_risk = np.arange(0, 101, 1)     # Наш выход (0-100)

    # --- ШАГ 2: "РИСУЕМ ГРАФИКИ" (ФУНКЦИИ ПРИНАДЛЕЖНОСТИ) ---
    
    # 1. ВХОД: Carbon Monoxide (CO)
    co = ctrl.Antecedent(universe_co, 'co')
    co['good']     = fuzz.trapmf(co.universe, [0, 0, 9000, 10000])
    co['moderate'] = fuzz.trapmf(co.universe, [9000, 10000, 12000, 13000])
    co['unhealthy'] = fuzz.trapmf(co.universe, [12000, 13000, 15000, 16000])
    co['hazardous'] = fuzz.trapmf(co.universe, [15000, 16000, 50000, 50000])

    # 2. ВХОД: Nitrogen Dioxide (NO2)
    no2 = ctrl.Antecedent(universe_no2, 'no2')
    no2['good']     = fuzz.trapmf(no2.universe, [0, 0, 80, 120])
    no2['moderate'] = fuzz.trapmf(no2.universe, [80, 120, 300, 400])
    no2['unhealthy'] = fuzz.trapmf(no2.universe, [300, 400, 600, 700])
    no2['hazardous'] = fuzz.trapmf(no2.universe, [600, 700, 2000, 2000])
    
    # 3. ВХОД: Sulphur Dioxide (SO2)
    so2 = ctrl.Antecedent(universe_so2, 'so2')
    so2['good']     = fuzz.trapmf(so2.universe, [0, 0, 80, 100])
    so2['moderate'] = fuzz.trapmf(so2.universe, [80, 100, 300, 400])
    so2['unhealthy'] = fuzz.trapmf(so2.universe, [300, 400, 700, 900])
    so2['hazardous'] = fuzz.trapmf(so2.universe, [700, 900, 2000, 2000])

    # 4. ВЫХОД: Gas_Risk (Риск от Газов)
    gas_risk = ctrl.Consequent(universe_risk, 'Gas_Risk')
    gas_risk['low']      = fuzz.trapmf(gas_risk.universe, [0, 0, 15, 30])
    gas_risk['medium']   = fuzz.trapmf(gas_risk.universe, [15, 30, 45, 60])
    gas_risk['high']     = fuzz.trapmf(gas_risk.universe, [45, 60, 75, 90])
    gas_risk['critical'] = fuzz.trapmf(gas_risk.universe, [75, 90, 100, 100])
    
    return [co, no2, so2], gas_risk


def define_other_variables():
    """
    Определяет "Вселенную" и "Графики" для Под-системы "Прочие".
    (Ozone и Ammonia)
    Возвращает 2 входа (Antecedents) и 1 выход (Consequent).
    """
    
    # --- ШАГ 1: ОПРЕДЕЛЯЕМ "ВСЕЛЕННУЮ" (ДИАПАЗОНЫ) ---
    # Диапазоны μg/m³ взяты из стандартов AQI
    universe_o3   = np.arange(0, 1001, 1)  # 0-1000 μg/m³ (Озон)
    universe_nh3  = np.arange(0, 1001, 1)  # 0-1000 μg/m³ (Аммиак)
    
    universe_risk = np.arange(0, 101, 1)    # Наш выход (0-100)

    # --- ШАГ 2: "РИСУЕМ ГРАФИКИ" (ФУНКЦИИ ПРИНАДЛЕЖНОСТИ) ---
    
    # 1. ВХОД: Ozone (O3) - "Фотохимический смог"
    o3 = ctrl.Antecedent(universe_o3, 'o3')
    o3['good']     = fuzz.trapmf(o3.universe, [0, 0, 80, 120])
    o3['moderate'] = fuzz.trapmf(o3.universe, [80, 120, 170, 190])
    o3['unhealthy'] = fuzz.trapmf(o3.universe, [170, 190, 230, 250])
    o3['hazardous'] = fuzz.trapmf(o3.universe, [230, 250, 1000, 1000])

    # 2. ВХОД: Ammonia (NH3) - "Аммиак"
    nh3 = ctrl.Antecedent(universe_nh3, 'nh3')
    # Для аммиака нет "жестких" стандартов AQI, используем лог. диапазоны
    nh3['low']    = fuzz.trapmf(nh3.universe, [0, 0, 50, 100])
    nh3['medium'] = fuzz.trapmf(nh3.universe, [50, 100, 200, 300])
    nh3['high']   = fuzz.trapmf(nh3.universe, [200, 300, 1000, 1000])

    # 3. ВЫХОД: Other_Risk (Риск от Прочих)
    other_risk = ctrl.Consequent(universe_risk, 'Other_Risk')
    other_risk['low']      = fuzz.trapmf(other_risk.universe, [0, 0, 15, 30])
    other_risk['medium']   = fuzz.trapmf(other_risk.universe, [15, 30, 45, 60])
    other_risk['high']     = fuzz.trapmf(other_risk.universe, [45, 60, 75, 90])
    other_risk['critical'] = fuzz.trapmf(other_risk.universe, [75, 90, 100, 100])
    
    return [o3, nh3], other_risk


def define_master_variables():
    """
    Определяет "Вселенную" и "Графики" для ГЛАВНОЙ (Мастер) Системы.
    Входы - это выходы из 3-х под-систем.
    Выходы - это финальный AQI и Рекомендация.
    """
    
    # --- ШАГ 1: ОПРЕДЕЛЯЕМ "ВСЕЛЕННУЮ" (ДИАПАЗОНЫ) ---
    
    # ВХОДЫ (шкала 0-100, "Риск")
    universe_subsystem_risk = np.arange(0, 101, 1)
    
    # ВЫХОД 1: Финальный AQI (шкала 0-500, как US AQI)
    universe_final_aqi = np.arange(0, 501, 1)
    
    # ВЫХОД 2: Рекомендация (шкала 0-10, условная)
    universe_recommendation = np.arange(0, 11, 1)

    # --- ШАГ 2: "РИСУЕМ ГРАФИКИ" (ФУНКЦИИ ПРИНАДЛЕЖНОСТИ) ---
    
    # 1. ВХОДЫ (3 шт, одинаковые графики для "Риска 0-100")
    particle_risk_in = ctrl.Antecedent(universe_subsystem_risk, 'particle_risk_in')
    gas_risk_in      = ctrl.Antecedent(universe_subsystem_risk, 'gas_risk_in')
    other_risk_in    = ctrl.Antecedent(universe_subsystem_risk, 'other_risk_in')
    
    for risk_input in [particle_risk_in, gas_risk_in, other_risk_in]:
        risk_input['low']      = fuzz.trapmf(risk_input.universe, [0, 0, 15, 30])
        risk_input['medium']   = fuzz.trapmf(risk_input.universe, [15, 30, 45, 60])
        risk_input['high']     = fuzz.trapmf(risk_input.universe, [45, 60, 75, 90])
        risk_input['critical'] = fuzz.trapmf(risk_input.universe, [75, 90, 100, 100])

    # 2. ВЫХОД 1: Final_AQI (0-500)
    final_aqi = ctrl.Consequent(universe_final_aqi, 'Final_AQI')
    final_aqi['good']      = fuzz.trapmf(final_aqi.universe, [0, 0, 40, 60])          # 0-50
    final_aqi['moderate']  = fuzz.trapmf(final_aqi.universe, [40, 60, 90, 110])       # 51-100
    final_aqi['unhealthy_S'] = fuzz.trapmf(final_aqi.universe, [90, 110, 140, 160]) # 101-150 (Sensitive)
    final_aqi['unhealthy'] = fuzz.trapmf(final_aqi.universe, [140, 160, 190, 210]) # 151-200
    final_aqi['hazardous'] = fuzz.trapmf(final_aqi.universe, [190, 210, 500, 500]) # 201+
    
    # 3. ВЫХОД 2: Recommendation (0-10)
    recommendation = ctrl.Consequent(universe_recommendation, 'Recommendation')
    # "Лингвистические" выходы
    recommendation['stay_home']  = fuzz.trimf(recommendation.universe, [0, 1, 3])
    recommendation['limit_activity'] = fuzz.trimf(recommendation.universe, [2, 4, 6])
    recommendation['go_out_safe']  = fuzz.trimf(recommendation.universe, [5, 7, 9])
    recommendation['perfect_day']  = fuzz.trimf(recommendation.universe, [7, 9, 10])

    
    return [particle_risk_in, gas_risk_in, other_risk_in], [final_aqi, recommendation]