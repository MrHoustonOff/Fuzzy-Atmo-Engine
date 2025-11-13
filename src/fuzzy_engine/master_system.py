# Файл: src/fuzzy_engine/master_system.py
"""
Модуль для Мастер-системы нечеткой логики.

Эта система является финальным агрегатором. Она принимает на вход
показатели риска от трех подсистем (частицы, газы, прочие) и вычисляет
два итоговых значения:
1.  Final_AQI: Числовой индекс качества воздуха по шкале 0-500.
2.  Recommendation: Условный индекс для вынесения текстовых рекомендаций.
"""
import skfuzzy.control as ctrl
from .membership_functions import define_master_variables


def get_master_rules(inputs: list, outputs: list) -> list[ctrl.Rule]:
    """
    Создает и возвращает базу правил для Мастер-системы.

    Правила построены по принципу иерархии: более высокий уровень риска
    от любой из подсистем имеет приоритет. Использование отрицаний (`~`)
    позволяет избежать конфликтов между правилами разных уровней.

    Args:
        inputs (list): Список входных переменных (Antecedents)
                       [particle_risk_in, gas_risk_in, other_risk_in].
        outputs (list): Список выходных переменных (Consequents)
                        [final_aqi, recommendation].

    Returns:
        list[ctrl.Rule]: Список правил для главной системы управления.
    """
    particle_risk_in, gas_risk_in, other_risk_in = inputs
    final_aqi, recommendation = outputs

    # Уровень 1: Критический. Если хотя бы один из входных рисков
    # является 'critical', итоговый результат будет 'hazardous'
    # и рекомендация - 'stay_home'.
    rule1 = ctrl.Rule(
        particle_risk_in['critical'] |
        gas_risk_in['critical'] |
        other_risk_in['critical'],
        (final_aqi['hazardous'], recommendation['stay_home'])
    )

    # Уровень 2: Высокий. Если хотя бы один риск 'high' и ни одного 'critical'.
    # Отрицание гарантирует, что это правило не сработает, если активно правило 1.
    rule2 = ctrl.Rule(
        (particle_risk_in['high'] | gas_risk_in['high'] | other_risk_in['high']) &
        (~particle_risk_in['critical'] &
         ~gas_risk_in['critical'] &
         ~other_risk_in['critical']),
        (final_aqi['unhealthy'], recommendation['limit_activity'])
    )

    # Уровень 3: Средний. Если хотя бы один риск 'medium' и ни одного 'high' или 'critical'.
    rule3 = ctrl.Rule(
        (particle_risk_in['medium'] | gas_risk_in['medium'] | other_risk_in['medium']) &
        (~particle_risk_in['high'] & ~gas_risk_in['high'] & ~other_risk_in['high']) &
        (~particle_risk_in['critical'] & ~gas_risk_in['critical'] & ~other_risk_in['critical']),
        (final_aqi['moderate'], recommendation['go_out_safe'])
    )

    # Уровень 3.5: Переходный. Смягчает переход от 'low' к 'medium'.
    # Если одна подсистема показывает низкий риск, а другая - средний,
    # итоговый результат также будет 'moderate'.
    rule3_5 = ctrl.Rule(
        ((particle_risk_in['low'] & gas_risk_in['medium']) |
         (particle_risk_in['medium'] & gas_risk_in['low']) |
         (particle_risk_in['low'] & other_risk_in['medium']) |
         (particle_risk_in['medium'] & other_risk_in['low']) |
         (gas_risk_in['low'] & other_risk_in['medium']) |
         (gas_risk_in['medium'] & other_risk_in['low'])) &
        (~particle_risk_in['high'] & ~gas_risk_in['high'] & ~other_risk_in['high']) &
        (~particle_risk_in['critical'] & ~gas_risk_in['critical'] & ~other_risk_in['critical']),
        (final_aqi['moderate'], recommendation['go_out_safe'])
    )

    # Уровень 4: Низкий. Самое строгое правило, которое активируется,
    # только если все три входных риска находятся на уровне 'low'.
    rule4 = ctrl.Rule(
        particle_risk_in['low'] &
        gas_risk_in['low'] &
        other_risk_in['low'],
        (final_aqi['good'], recommendation['perfect_day'])
    )

    return [rule1, rule2, rule3, rule3_5, rule4]


def create_master_engine() -> ctrl.ControlSystem:
    """
    Собирает и возвращает главную систему управления (Мастер-систему).

    Объединяет переменные, функции принадлежности и правила в готовый
    "движок" нечеткой логики.

    Returns:
        ctrl.ControlSystem: Готовая к использованию Мастер-система.
    """
    # Шаг 1: Определение входных и выходных переменных.
    inputs, outputs = define_master_variables()

    # Шаг 2: Создание базы правил.
    rules = get_master_rules(inputs, outputs)

    # Шаг 3: Сборка и возврат системы управления.
    master_engine = ctrl.ControlSystem(rules)
    return master_engine
