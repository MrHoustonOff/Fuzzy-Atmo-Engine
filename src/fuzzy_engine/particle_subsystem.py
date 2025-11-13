# Файл: src/fuzzy_engine/particle_subsystem.py
"""
Модуль подсистемы нечеткой логики для оценки риска от твердых частиц.

Эта подсистема анализирует такие показатели, как PM2.5, PM10,
аэрозольная оптическая толщина (AOD) и концентрация пыли,
чтобы вычислить единый показатель риска 'Particle_Risk'.
"""
import skfuzzy.control as ctrl
from .membership_functions import define_particle_variables


def get_particle_rules(inputs: list, output: ctrl.Consequent) -> list[ctrl.Rule]:
    """
    Создает и возвращает базу правил для подсистемы оценки риска от частиц.

    Правила определяют взаимосвязь между входными концентрациями
    загрязнителей и итоговым уровнем риска.

    Args:
        inputs (list): Список входных переменных (Antecedents)
                       [pm2_5, pm10, aod, dust].
        output (ctrl.Consequent): Выходная переменная (Consequent) particle_risk.

    Returns:
        list[ctrl.Rule]: Список правил для системы управления.
    """
    pm2_5, pm10, aod, dust = inputs
    particle_risk = output

    # Правило 1-2: Критический риск. Активируются, если концентрация PM2.5
    # или PM10 достигает опасного уровня. Имеют наивысший приоритет.
    rule1 = ctrl.Rule(pm2_5['hazardous'], particle_risk['critical'])
    rule2 = ctrl.Rule(pm10['hazardous'], particle_risk['critical'])

    # Правило 3-4: Высокий риск. Активируются при "нездоровом" уровне PM2.5 или PM10.
    rule3 = ctrl.Rule(pm2_5['unhealthy'], particle_risk['high'])
    rule4 = ctrl.Rule(pm10['unhealthy'], particle_risk['high'])

    # Правило 5-6: Правила, связанные с пылью и мутностью атмосферы (AOD).
    rule5 = ctrl.Rule(dust['high'] & aod['high'], particle_risk['high'])
    rule6 = ctrl.Rule(dust['medium'] & aod['medium'], particle_risk['medium'])

    # Правило 7-8: Средний риск. Активируются при умеренных уровнях PM.
    rule7 = ctrl.Rule(pm2_5['moderate'] | pm10['moderate'], particle_risk['medium'])
    rule8 = ctrl.Rule(pm2_5['moderate'] & pm10['moderate'], particle_risk['medium'])

    # Правило 9: Идеальные условия. Низкий риск устанавливается только тогда,
    # когда все четыре показателя находятся в пределах нормы.
    rule9 = ctrl.Rule(
        pm2_5['good'] & pm10['good'] & aod['low'] & dust['low'],
        particle_risk['low']
    )

    # Правило 10: Упрощенное правило для хороших условий,
    # если известны только основные показатели.
    rule10 = ctrl.Rule(pm2_5['good'] & pm10['good'], particle_risk['low'])

    return [
        rule1, rule2, rule3, rule4, rule5,
        rule6, rule7, rule8, rule9, rule10
    ]


def create_particle_engine() -> ctrl.ControlSystem:
    """
    Собирает и возвращает систему управления для подсистемы "Частицы".

    Эта функция объединяет переменные, функции принадлежности и базу правил
    в единый "движок" нечеткой логики.

    Returns:
        ctrl.ControlSystem: Готовая к использованию система управления.
    """
    # Шаг 1: Определение переменных и их функций принадлежности.
    inputs, output = define_particle_variables()

    # Шаг 2: Создание базы правил на основе этих переменных.
    rules = get_particle_rules(inputs, output)

    # Шаг 3: Сборка и возврат системы управления.
    particle_engine = ctrl.ControlSystem(rules)
    return particle_engine
