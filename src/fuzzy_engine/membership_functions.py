# Файл: src/fuzzy_engine/membership_functions.py
"""
Центральный модуль для определения всех переменных и функций принадлежности.

Этот файл служит "словарём" для системы нечеткой логики. В нём задаются
числовые диапазоны (Вселенные) для всех входных и выходных переменных,
а также определяются лингвистические термы (например, 'good', 'high')
с помощью функций принадлежности (например, трапециевидных).

Структура разделена по подсистемам для ясности и удобства дальнейшего
анализа или создания отчетов. Диапазоны для загрязнителей основаны на
стандартах Индекса качества воздуха (AQI) от Агентства по охране
окружающей среды США (EPA).
"""
import numpy as np
import skfuzzy as fuzz
import skfuzzy.control as ctrl

# Общая "Вселенная" для выходных переменных риска подсистем (шкала 0-100).
# Используется в подсистемах частиц, газов и прочих.
UNIVERSE_RISK = np.arange(0, 101, 1)


def define_particle_variables() -> tuple[list, ctrl.Consequent]:
    """
    Определяет переменные и функции принадлежности для подсистемы "Частицы".

    Returns:
        tuple[list, ctrl.Consequent]: Кортеж, содержащий:
            - Список из 4-х входных переменных (Antecedents):
              [pm2_5, pm10, aod, dust].
            - Одна выходная переменная (Consequent): particle_risk.
    """
    # --- 1. Определение "Вселенных" (диапазонов) для входов ---
    universe_pm2_5 = np.arange(0, 501, 1)    # 0-500 мкг/м³
    universe_pm10 = np.arange(0, 601, 1)    # 0-600 мкг/м³
    universe_aod = np.arange(0, 5.1, 0.1)  # 0-5 (Аэрозольная оптическая толщина)
    universe_dust = np.arange(0, 1001, 1)   # 0-1000 мкг/м³

    # --- 2. Определение входных переменных (Antecedents) ---

    # PM2.5 (мелкодисперсные частицы, наиболее опасные)
    pm2_5 = ctrl.Antecedent(universe_pm2_5, 'pm2_5')
    pm2_5['good'] = fuzz.trapmf(pm2_5.universe, [0, 0, 10, 15])
    pm2_5['moderate'] = fuzz.trapmf(pm2_5.universe, [10, 15, 30, 40])
    pm2_5['unhealthy'] = fuzz.trapmf(pm2_5.universe, [30, 40, 140, 160])
    pm2_5['hazardous'] = fuzz.trapmf(pm2_5.universe, [140, 160, 500, 500])

    # PM10 (крупнодисперсные частицы)
    pm10 = ctrl.Antecedent(universe_pm10, 'pm10')
    pm10['good'] = fuzz.trapmf(pm10.universe, [0, 0, 40, 60])
    pm10['moderate'] = fuzz.trapmf(pm10.universe, [40, 60, 140, 170])
    pm10['unhealthy'] = fuzz.trapmf(pm10.universe, [140, 170, 340, 360])
    pm10['hazardous'] = fuzz.trapmf(pm10.universe, [340, 360, 600, 600])

    # AOD (Aerosol Optical Depth - косвенный показатель загрязнения)
    aod = ctrl.Antecedent(universe_aod, 'aod')
    aod['low'] = fuzz.trapmf(aod.universe, [0, 0, 0.5, 1])
    aod['medium'] = fuzz.trapmf(aod.universe, [0.5, 1, 2, 3])
    aod['high'] = fuzz.trapmf(aod.universe, [2, 3, 5, 5])

    # Dust (Пыль)
    dust = ctrl.Antecedent(universe_dust, 'dust')
    dust['low'] = fuzz.trapmf(dust.universe, [0, 0, 50, 150])
    dust['medium'] = fuzz.trapmf(dust.universe, [50, 150, 300, 450])
    dust['high'] = fuzz.trapmf(dust.universe, [300, 450, 1000, 1000])

    # --- 3. Определение выходной переменной (Consequent) ---
    particle_risk = ctrl.Consequent(UNIVERSE_RISK, 'Particle_Risk')
    particle_risk['low'] = fuzz.trapmf(particle_risk.universe, [0, 0, 15, 30])
    particle_risk['medium'] = fuzz.trapmf(particle_risk.universe, [15, 30, 45, 60])
    particle_risk['high'] = fuzz.trapmf(particle_risk.universe, [45, 60, 75, 90])
    particle_risk['critical'] = fuzz.trapmf(particle_risk.universe, [75, 90, 100, 100])

    return [pm2_5, pm10, aod, dust], particle_risk


def define_gas_variables() -> tuple[list, ctrl.Consequent]:
    """
    Определяет переменные и функции принадлежности для подсистемы "Газы".

    Returns:
        tuple[list, ctrl.Consequent]: Кортеж, содержащий:
            - Список из 3-х входных переменных (Antecedents): [co, no2, so2].
            - Одна выходная переменная (Consequent): gas_risk.
    """
    # --- 1. Определение "Вселенных" для входов ---
    universe_co = np.arange(0, 50001, 10)  # 0-50,000 мкг/м³
    universe_no2 = np.arange(0, 2001, 1)   # 0-2,000 мкг/м³
    universe_so2 = np.arange(0, 2001, 1)   # 0-2,000 мкг/м³

    # --- 2. Определение входных переменных (Antecedents) ---

    # CO (Угарный газ)
    co = ctrl.Antecedent(universe_co, 'co')
    co['good'] = fuzz.trapmf(co.universe, [0, 0, 9000, 10000])
    co['moderate'] = fuzz.trapmf(co.universe, [9000, 10000, 12000, 13000])
    co['unhealthy'] = fuzz.trapmf(co.universe, [12000, 13000, 15000, 16000])
    co['hazardous'] = fuzz.trapmf(co.universe, [15000, 16000, 50000, 50000])

    # NO2 (Диоксид азота)
    no2 = ctrl.Antecedent(universe_no2, 'no2')
    no2['good'] = fuzz.trapmf(no2.universe, [0, 0, 80, 120])
    no2['moderate'] = fuzz.trapmf(no2.universe, [80, 120, 300, 400])
    no2['unhealthy'] = fuzz.trapmf(no2.universe, [300, 400, 600, 700])
    no2['hazardous'] = fuzz.trapmf(no2.universe, [600, 700, 2000, 2000])

    # SO2 (Диоксид серы)
    so2 = ctrl.Antecedent(universe_so2, 'so2')
    so2['good'] = fuzz.trapmf(so2.universe, [0, 0, 80, 100])
    so2['moderate'] = fuzz.trapmf(so2.universe, [80, 100, 300, 400])
    so2['unhealthy'] = fuzz.trapmf(so2.universe, [300, 400, 700, 900])
    so2['hazardous'] = fuzz.trapmf(so2.universe, [700, 900, 2000, 2000])

    # --- 3. Определение выходной переменной (Consequent) ---
    gas_risk = ctrl.Consequent(UNIVERSE_RISK, 'Gas_Risk')
    gas_risk['low'] = fuzz.trapmf(gas_risk.universe, [0, 0, 15, 30])
    gas_risk['medium'] = fuzz.trapmf(gas_risk.universe, [15, 30, 45, 60])
    gas_risk['high'] = fuzz.trapmf(gas_risk.universe, [45, 60, 75, 90])
    gas_risk['critical'] = fuzz.trapmf(gas_risk.universe, [75, 90, 100, 100])

    return [co, no2, so2], gas_risk


def define_other_variables() -> tuple[list, ctrl.Consequent]:
    """
    Определяет переменные и функции принадлежности для подсистемы "Прочие".

    Returns:
        tuple[list, ctrl.Consequent]: Кортеж, содержащий:
            - Список из 2-х входных переменных (Antecedents): [o3, nh3].
            - Одна выходная переменная (Consequent): other_risk.
    """
    # --- 1. Определение "Вселенных" для входов ---
    universe_o3 = np.arange(0, 1001, 1)   # 0-1000 мкг/м³ (Озон)
    universe_nh3 = np.arange(0, 1001, 1)  # 0-1000 мкг/м³ (Аммиак)

    # --- 2. Определение входных переменных (Antecedents) ---

    # O3 (Озон - основной компонент фотохимического смога)
    o3 = ctrl.Antecedent(universe_o3, 'o3')
    o3['good'] = fuzz.trapmf(o3.universe, [0, 0, 80, 120])
    o3['moderate'] = fuzz.trapmf(o3.universe, [80, 120, 170, 190])
    o3['unhealthy'] = fuzz.trapmf(o3.universe, [170, 190, 230, 250])
    o3['hazardous'] = fuzz.trapmf(o3.universe, [230, 250, 1000, 1000])

    # NH3 (Аммиак)
    # Стандарты AQI для аммиака менее строгие, используются экспертные диапазоны.
    nh3 = ctrl.Antecedent(universe_nh3, 'nh3')
    nh3['low'] = fuzz.trapmf(nh3.universe, [0, 0, 50, 100])
    nh3['medium'] = fuzz.trapmf(nh3.universe, [50, 100, 200, 300])
    nh3['high'] = fuzz.trapmf(nh3.universe, [200, 300, 1000, 1000])

    # --- 3. Определение выходной переменной (Consequent) ---
    other_risk = ctrl.Consequent(UNIVERSE_RISK, 'Other_Risk')
    other_risk['low'] = fuzz.trapmf(other_risk.universe, [0, 0, 15, 30])
    other_risk['medium'] = fuzz.trapmf(other_risk.universe, [15, 30, 45, 60])
    other_risk['high'] = fuzz.trapmf(other_risk.universe, [45, 60, 75, 90])
    other_risk['critical'] = fuzz.trapmf(other_risk.universe, [75, 90, 100, 100])

    return [o3, nh3], other_risk


def define_master_variables() -> tuple[list, list]:
    """
    Определяет переменные для главной Мастер-системы.

    Входами служат выходные риски из трех подсистем.
    Выходами являются финальный AQI и условный индекс для рекомендаций.

    Returns:
        tuple[list, list]: Кортеж, содержащий:
            - Список из 3-х входных переменных (Antecedents):
              [particle_risk_in, gas_risk_in, other_risk_in].
            - Список из 2-х выходных переменных (Consequents):
              [final_aqi, recommendation].
    """
    # --- 1. Определение "Вселенных" ---
    # Вход: унифицированный риск от подсистем (шкала 0-100)
    universe_subsystem_risk = np.arange(0, 101, 1)
    # Выход 1: финальный AQI (шкала 0-500, по аналогии с US AQI)
    universe_final_aqi = np.arange(0, 501, 1)
    # Выход 2: индекс рекомендации (условная шкала 0-10)
    universe_recommendation = np.arange(0, 11, 1)

    # --- 2. Определение входных переменных (Antecedents) ---
    particle_risk_in = ctrl.Antecedent(universe_subsystem_risk, 'particle_risk_in')
    gas_risk_in = ctrl.Antecedent(universe_subsystem_risk, 'gas_risk_in')
    other_risk_in = ctrl.Antecedent(universe_subsystem_risk, 'other_risk_in')

    # Функции принадлежности для входов-рисков идентичны
    for risk_input in [particle_risk_in, gas_risk_in, other_risk_in]:
        risk_input['low'] = fuzz.trapmf(risk_input.universe, [0, 0, 15, 30])
        risk_input['medium'] = fuzz.trapmf(risk_input.universe, [15, 30, 45, 60])
        risk_input['high'] = fuzz.trapmf(risk_input.universe, [45, 60, 75, 90])
        risk_input['critical'] = fuzz.trapmf(risk_input.universe, [75, 90, 100, 100])

    # --- 3. Определение выходных переменных (Consequents) ---

    # Выход 1: Final_AQI (0-500)
    final_aqi = ctrl.Consequent(universe_final_aqi, 'Final_AQI')
    final_aqi['good'] = fuzz.trapmf(final_aqi.universe, [0, 0, 40, 60])
    final_aqi['moderate'] = fuzz.trapmf(final_aqi.universe, [40, 60, 90, 110])
    final_aqi['unhealthy_S'] = fuzz.trapmf(final_aqi.universe, [90, 110, 140, 160])
    final_aqi['unhealthy'] = fuzz.trapmf(final_aqi.universe, [140, 160, 190, 210])
    final_aqi['hazardous'] = fuzz.trapmf(final_aqi.universe, [190, 210, 500, 500])

    # Выход 2: Recommendation (0-10)
    recommendation = ctrl.Consequent(universe_recommendation, 'Recommendation')
    # Используем треугольные функции для более "четкого" пика рекомендации
    recommendation['stay_home'] = fuzz.trimf(recommendation.universe, [0, 1, 3])
    recommendation['limit_activity'] = fuzz.trimf(recommendation.universe, [2, 4, 6])
    recommendation['go_out_safe'] = fuzz.trimf(recommendation.universe, [5, 7, 9])
    recommendation['perfect_day'] = fuzz.trimf(recommendation.universe, [7, 9, 10])

    return [particle_risk_in, gas_risk_in, other_risk_in], [final_aqi, recommendation]