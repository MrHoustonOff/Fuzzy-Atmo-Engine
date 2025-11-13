# Файл: src/fuzzy_engine/other_subsystem.py

import skfuzzy.control as ctrl

# Импортируем "графики" для "Прочих"
from .membership_functions import define_other_variables

def get_other_rules(inputs, output):
    """
    (ШАГ 3) Создаем "Базу Правил" для "Прочих".
    Озон (O3) - главный "актор" в этой группе.
    """
    o3, nh3 = inputs
    other_risk = output
    
    # --- КРИТИЧЕСКИЕ (Атомарные) ---
    rule1 = ctrl.Rule(o3['hazardous'], other_risk['critical'])
    
    # --- ВЫСОКИЙ РИСК (Атомарные) ---
    rule2 = ctrl.Rule(o3['unhealthy'], other_risk['high'])
    
    # --- СРЕДНИЙ РИСК (Аммиак) ---
    # Аммиак (NH3) менее "опасен" для общего AQI, 
    # но мы не можем его игнорировать.
    rule3 = ctrl.Rule(nh3['high'], other_risk['medium'])
    
    # --- СРЕДНИЙ РИСК (Озон) ---
    rule4 = ctrl.Rule(o3['moderate'], other_risk['medium'])

    # --- КОМБИНИРОВАННЫЙ РИСК ---
    rule5 = ctrl.Rule(o3['moderate'] & nh3['high'], other_risk['high'])
    
    # --- НИЗКИЙ РИСК (Идеальный случай) ---
    rule6 = ctrl.Rule(o3['good'] & nh3['low'], other_risk['low'])

    return [rule1, rule2, rule3, rule4, rule5, rule6]

def create_other_engine():
    """
    (ШАГ 4) "Сборка"
    Собирает "движок" для "Прочей" под-системы.
    """
    
    # Шаг 1+2: Получаем переменные и их графики
    inputs, output = define_other_variables()
    
    # Шаг 3: Получаем "мозг" (базу правил)
    rules = get_other_rules(inputs, output)
    
    # Шаг 4: Собираем "Движок Мамдани"
    other_engine = ctrl.ControlSystem(rules)
    
    return other_engine