# Файл: src/fuzzy_engine/particle_subsystem.py

import skfuzzy.control as ctrl

# Импортируем наши "графики" из "мини-базы матана"
from .membership_functions import define_particle_variables

def get_particle_rules(inputs, output):
    """
    Создаем Базу Правил для Частиц.
    """
    pm2_5, pm10, aod, dust = inputs
    particle_risk = output

    # --- КРИТИЧЕСКИЕ (Атомарные) Правила ---
    # Если ХОТЯ БЫ ОДИН главный показатель "опасный", риск - КРИТИЧЕСКИЙ.
    rule1 = ctrl.Rule(pm2_5['hazardous'], particle_risk['critical'])
    rule2 = ctrl.Rule(pm10['hazardous'], particle_risk['critical'])

    # --- ВЫСОКИЙ РИСК (Атомарные) ---
    rule3 = ctrl.Rule(pm2_5['unhealthy'], particle_risk['high'])
    rule4 = ctrl.Rule(pm10['unhealthy'], particle_risk['high'])

    # --- "ПЫЛЕВЫЕ" (Составные) Правила ---
    rule5 = ctrl.Rule(dust['high'] & aod['high'], particle_risk['high'])
    rule6 = ctrl.Rule(dust['medium'] & aod['medium'], particle_risk['medium'])

    # --- СРЕДНИЙ РИСК (Составные) ---
    rule7 = ctrl.Rule(pm2_5['moderate'] | pm10['moderate'], particle_risk['medium'])
    rule8 = ctrl.Rule(pm2_5['moderate'] & pm10['moderate'], particle_risk['medium'])

    # --- "ИДЕАЛЬНЫЕ" (Составные) Правила ---
    rule9 = ctrl.Rule(
        pm2_5['good'] &
        pm10['good'] &
        aod['low'] &
        dust['low'],
        particle_risk['low']
    )

    # --- ПРОСТО ХОРОШИЕ ---
    rule10 = ctrl.Rule(pm2_5['good'] & pm10['good'], particle_risk['low'])

    # Собираем все 10 правил в список
    return [rule1, rule2, rule3, rule4, rule5, rule6,
            rule7, rule8, rule9, rule10]


def create_particle_engine():
    """
    Собирает все компоненты в единый "движок" (ControlSystem).
    """

    inputs, output = define_particle_variables()

    rules = get_particle_rules(inputs, output)

    particle_engine = ctrl.ControlSystem(rules)

    # TODO для Этапа 5 (Отчет):
    # Чтобы посмотреть "секси график" pm2_5:
    # pm2_5.view()
    # (Нам понадобится matplotlib.pyplot.show())

    return particle_engine
