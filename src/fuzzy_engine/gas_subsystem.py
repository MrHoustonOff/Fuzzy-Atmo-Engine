import skfuzzy.control as ctrl

# Импортируем "графики" для Газов
from .membership_functions import define_gas_variables

def get_gas_rules(inputs, output):
    """
    (ШАГ 3) Создаем "Базу Правил" для Газов.
    (ВЕРСИЯ 2.0 - "Патч" от "Войны Правил")
    """
    co, no2, so2 = inputs
    gas_risk = output
    
    # --- КРИТИЧЕСКИЕ (Атомарные) ---
    # Эти правила "старшие".
    rule1 = ctrl.Rule(co['hazardous'] | no2['hazardous'] | so2['hazardous'], 
                      gas_risk['critical'])
    
    # --- ВЫСОКИЙ РИСК (Атомарные) ---
    rule2 = ctrl.Rule(co['unhealthy'] | no2['unhealthy'] | so2['unhealthy'],
                      gas_risk['high'])

    # --- СРЕДНИЙ РИСК (Составные) ---
    rule3 = ctrl.Rule(co['moderate'] | no2['moderate'] | so2['moderate'],
                      gas_risk['medium'])
    
    # --- НИЗКИЙ РИСК (Идеальный и СТРОГИЙ случай) ---
    # "Ленивые" rule5 и rule6 (которые вызывали "войну") - УДАЛЕНЫ.
    # Оставляем ТОЛЬКО "строгое" правило:
    rule4 = ctrl.Rule(co['good'] & no2['good'] & so2['good'],
                      gas_risk['low'])
    
    # Мы УДАЛИЛИ "ленивые" правила, которые "конфликтовали" с 'hazardous'.
    # Теперь 'rule1' (Critical) "победит", а 'rule4' (Low) не "включится",
    # потому что 'so2' - НЕ 'good'.
    return [rule1, rule2, rule3, rule4]

def create_gas_engine():
    """
    (ШАГ 4) "Сборка"
    Собирает "движок" для Газовой под-системы.
    """
    
    # Шаг 1+2: Получаем переменные и их графики
    inputs, output = define_gas_variables()
    
    # Шаг 3: Получаем "мозг" (базу правил)
    rules = get_gas_rules(inputs, output)
    
    # Шаг 4: Собираем "Движок Мамдани"
    gas_engine = ctrl.ControlSystem(rules)
    
    return gas_engine