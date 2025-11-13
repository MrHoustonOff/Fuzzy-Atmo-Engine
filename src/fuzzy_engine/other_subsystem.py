# Файл: src/fuzzy_engine/other_subsystem.py
"""
Модуль подсистемы для оценки риска от прочих загрязнителей.

В данной реализации анализирует концентрации озона (O3) и аммиака (NH3)
для вычисления единого показателя 'Other_Risk'.
"""
import skfuzzy.control as ctrl
from .membership_functions import define_other_variables


def get_other_rules(inputs: list, output: ctrl.Consequent) -> list[ctrl.Rule]:
    """
    Создает и возвращает базу правил для подсистемы "Прочие".

    В этой подсистеме озон (O3) является основным фактором, определяющим
    высокие уровни риска, в то время как аммиак (NH3) вносит
    дополнительный вклад в средние и высокие уровни.

    Args:
        inputs (list): Список входных переменных (Antecedents) [o3, nh3].
        output (ctrl.Consequent): Выходная переменная (Consequent) other_risk.

    Returns:
        list[ctrl.Rule]: Список правил для системы управления.
    """
    o3, nh3 = inputs
    other_risk = output

    # Правило 1: Критический риск, если озон достигает опасного уровня.
    rule1 = ctrl.Rule(o3['hazardous'], other_risk['critical'])

    # Правило 2: Высокий риск, если озон на "нездоровом" уровне.
    rule2 = ctrl.Rule(o3['unhealthy'], other_risk['high'])

    # Правило 3: Средний риск из-за высокой концентрации аммиака.
    rule3 = ctrl.Rule(nh3['high'], other_risk['medium'])

    # Правило 4: Средний риск из-за умеренной концентрации озона.
    rule4 = ctrl.Rule(o3['moderate'], other_risk['medium'])

    # Правило 5: Комбинированное правило. Умеренный озон и высокий
    # уровень аммиака вместе приводят к высокому риску.
    rule5 = ctrl.Rule(o3['moderate'] & nh3['high'], other_risk['high'])

    # Правило 6: Низкий риск, если оба показателя в норме.
    rule6 = ctrl.Rule(o3['good'] & nh3['low'], other_risk['low'])

    return [rule1, rule2, rule3, rule4, rule5, rule6]


def create_other_engine() -> ctrl.ControlSystem:
    """
    Собирает и возвращает систему управления для подсистемы "Прочие".

    Объединяет переменные, функции принадлежности и правила в готовый
    "движок" нечеткой логики.

    Returns:
        ctrl.ControlSystem: Готовая к использованию система управления.
    """
    # Шаг 1: Определение переменных и их функций принадлежности.
    inputs, output = define_other_variables()

    # Шаг 2: Создание базы правил.
    rules = get_other_rules(inputs, output)

    # Шаг 3: Сборка и возврат системы управления.
    other_engine = ctrl.ControlSystem(rules)
    return other_engine
