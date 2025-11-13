# Файл: src/fuzzy_engine/gas_subsystem.py
"""
Модуль подсистемы нечеткой логики для оценки риска от газов.

Анализирует концентрации угарного газа (CO), диоксида азота (NO2)
и диоксида серы (SO2) для вычисления единого показателя 'Gas_Risk'.
"""
import skfuzzy.control as ctrl
from .membership_functions import define_gas_variables


def get_gas_rules(inputs: list, output: ctrl.Consequent) -> list[ctrl.Rule]:
    """
    Создает и возвращает базу правил для подсистемы оценки риска от газов.

    Структура правил обеспечивает приоритет более опасных состояний.
    Например, если один из газов достигает уровня 'hazardous',
    результирующий риск будет 'critical', независимо от других показателей.

    Args:
        inputs (list): Список входных переменных (Antecedents) [co, no2, so2].
        output (ctrl.Consequent): Выходная переменная (Consequent) gas_risk.

    Returns:
        list[ctrl.Rule]: Список правил для системы управления.
    """
    co, no2, so2 = inputs
    gas_risk = output

    # Правило 1: Критический риск. Если хотя бы один газ 'hazardous'.
    rule1 = ctrl.Rule(
        co['hazardous'] | no2['hazardous'] | so2['hazardous'],
        gas_risk['critical']
    )

    # Правило 2: Высокий риск. Если хотя бы один газ 'unhealthy'.
    rule2 = ctrl.Rule(
        co['unhealthy'] | no2['unhealthy'] | so2['unhealthy'],
        gas_risk['high']
    )

    # Правило 3: Средний риск. Если хотя бы один газ 'moderate'.
    rule3 = ctrl.Rule(
        co['moderate'] | no2['moderate'] | so2['moderate'],
        gas_risk['medium']
    )

    # Правило 4: Низкий риск. Это правило самое строгое: активируется,
    # только если все три газа находятся в категории 'good'.
    rule4 = ctrl.Rule(
        co['good'] & no2['good'] & so2['good'],
        gas_risk['low']
    )

    return [rule1, rule2, rule3, rule4]


def create_gas_engine() -> ctrl.ControlSystem:
    """
    Собирает и возвращает систему управления для подсистемы "Газы".

    Объединяет переменные, функции принадлежности и правила в готовый
    "движок" нечеткой логики.

    Returns:
        ctrl.ControlSystem: Готовая к использованию система управления.
    """
    # Шаг 1: Определение переменных и их функций принадлежности.
    inputs, output = define_gas_variables()

    # Шаг 2: Создание базы правил.
    rules = get_gas_rules(inputs, output)

    # Шаг 3: Сборка и возврат системы управления.
    gas_engine = ctrl.ControlSystem(rules)
    return gas_engine
