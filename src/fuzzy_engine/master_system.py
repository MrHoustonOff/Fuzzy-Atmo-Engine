# Файл: src/fuzzy_engine/master_system.py

import skfuzzy.control as ctrl

# Импортируем "графики" для "Мастера"
from .membership_functions import define_master_variables


def get_master_rules(inputs, outputs):
    """
    (ШАГ 3) Создаем "Базу Правил" для ГЛАВНОЙ Системы.
    (ВЕРСИЯ 3.1.1 — стабильная. Сбалансированные реалистичные правила, нейминг адаптирован.)
    """
    particle_risk_in, gas_risk_in, other_risk_in = inputs
    final_aqi, recommendation = outputs

    # --- УРОВЕНЬ 1: КРИТИЧЕСКИЙ ---
    rule1 = ctrl.Rule(
        particle_risk_in['critical'] |
        gas_risk_in['critical'] |
        other_risk_in['critical'],
        (final_aqi['hazardous'], recommendation['stay_home'])
    )

    # --- УРОВЕНЬ 2: ВЫСОКИЙ ---
    rule2 = ctrl.Rule(
        (particle_risk_in['high'] | gas_risk_in['high'] | other_risk_in['high']) &
        (~particle_risk_in['critical'] &
         ~gas_risk_in['critical'] &
         ~other_risk_in['critical']),
        (final_aqi['unhealthy'], recommendation['limit_activity'])
    )

    # --- УРОВЕНЬ 3: СРЕДНИЙ ---
    # Реалистичный "moderate" уровень — близко к EPA (≈ 50–100 AQI)
    rule3 = ctrl.Rule(
        (particle_risk_in['medium'] | gas_risk_in['medium'] | other_risk_in['medium']) &
        (~particle_risk_in['high'] &
         ~gas_risk_in['high'] &
         ~other_risk_in['high']) &
        (~particle_risk_in['critical'] &
         ~gas_risk_in['critical'] &
         ~other_risk_in['critical']),
        (final_aqi['moderate'], recommendation['go_out_safe'])
    )

    # --- УРОВЕНЬ 3.5: ПЕРЕХОДНЫЙ (Low + Medium) ---
    # Смягчает переход между "good" и "moderate"
    rule3_5 = ctrl.Rule(
        ((particle_risk_in['low'] & gas_risk_in['medium']) |
         (particle_risk_in['medium'] & gas_risk_in['low']) |
         (particle_risk_in['low'] & other_risk_in['medium']) |
         (particle_risk_in['medium'] & other_risk_in['low']) |
         (gas_risk_in['low'] & other_risk_in['medium']) |
         (gas_risk_in['medium'] & other_risk_in['low'])) &
        (~particle_risk_in['high'] &
         ~gas_risk_in['high'] &
         ~other_risk_in['high']) &
        (~particle_risk_in['critical'] &
         ~gas_risk_in['critical'] &
         ~other_risk_in['critical']),
        (final_aqi['moderate'], recommendation['go_out_safe'])
    )

    # --- УРОВЕНЬ 4: НИЗКИЙ (Идеальный) ---
    rule4 = ctrl.Rule(
        particle_risk_in['low'] &
        gas_risk_in['low'] &
        other_risk_in['low'],
        (final_aqi['good'], recommendation['perfect_day'])
    )

    # Возвращаем весь набор правил
    return [rule1, rule2, rule3, rule3_5, rule4]


def create_master_engine():
    """
    (ШАГ 4) "Сборка"
    Собирает ГЛАВНЫЙ "движок".
    """
    # Шаг 1+2: Получаем переменные и их графики
    inputs, outputs = define_master_variables()

    # Шаг 3: Получаем "мозг" (базу правил)
    rules = get_master_rules(inputs, outputs)

    # Шаг 4: Собираем "Движок Мамдани"
    master_engine = ctrl.ControlSystem(rules)

    return master_engine
