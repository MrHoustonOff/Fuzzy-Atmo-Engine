import time
import json  # (Оставляем для 'mock_data.json')
import random # (Оставляем для "будущих" "стульев")
from rich.panel import Panel
from rich.prompt import Prompt
from rich.pretty import Pretty
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
import skfuzzy.control as ctrl

from src.utils.logger import console
from src.api_client.client import AirQualityClient
from config import CURRENT_PARAMS, HOURLY_PARAMS

# "Чистые" импорты "матана"
from src.fuzzy_engine.particle_subsystem import create_particle_engine
from src.fuzzy_engine.gas_subsystem import create_gas_engine
from src.fuzzy_engine.other_subsystem import create_other_engine
from src.fuzzy_engine.master_system import create_master_engine
from src.fuzzy_engine.forecast_preprocessor import preprocess_hourly_data
from src.fuzzy_engine.forecast_system import create_forecast_engine



def print_autograph():
    autograph = r'''
                                    [blue]Made by:[/blue]
<-. (`-')     (`-')  (`-').->                       (`-').->(`-')                <-. (`-')_ 
   \(OO )_ <-.(OO )  (OO )__      .->        .->    ( OO)_  ( OO).->       .->      \( OO) )
,--./  ,-.),------,),--. ,'-'(`-')----. ,--.(,--.  (_)--\_) /    '._  (`-')----. ,--./ ,--/ 
|   `.'   ||   /`. '|  | |  |( OO).-.  '|  | |(`-')/    _ / |'--...__)( OO).-.  '|   \ |  | 
|  |'.'|  ||  |_.' ||  `-'  |( _) | |  ||  | |(OO )\_..`--. `--.  .--'( _) | |  ||  . '|  |)
|  |   |  ||  .   .'|  .-.  | \|  |)|  ||  | | |  \.-._)   \   |  |    \|  |)|  ||  |\    | 
|  |   |  ||  |\  \ |  | |  |  '  '-'  '\  '-'(_ .'\       /   |  |     '  '-'  '|  | \   | 
`--'   `--'`--' '--'`--' `--'   `-----'  `-----'    `-----'    `--'      `-----' `--'  `--' 
    '''
    console.print(Panel.fit(autograph, style="bold"))


def get_coordinates() -> (float, float):
    console.print(Panel.fit(
        "Нам нужны координаты. \nТыкни в карту и получи их тут: [bold link=https://www.latlong.net/]https://www.latlong.net/[/]",
        title="[yellow]Ввод данных[/yellow]",
        padding=(1, 2)
    ))

    while True:
        try:
            lat_str = Prompt.ask("   [cyan]Введите Широту (Latitude)[/cyan]")
            latitude = float(lat_str)
            if not -90 <= latitude <= 90:
                raise ValueError("Широта должна быть в диапазоне [-90, 90].")
            break
        except ValueError as e:
            console.print(f"[bold red]Ошибка![/] {e}. Попробуйте еще раз.")

    while True:
        try:
            lon_str = Prompt.ask("   [cyan]Введите Долготу (Longitude)[/cyan]")
            longitude = float(lon_str)
            if not -180 <= longitude <= 180:
                raise ValueError("Долгота должна быть в диапазоне [-180, 180].")
            break
        except ValueError as e:
            console.print(f"[bold red]Ошибка![/] {e}. Попробуйте еще раз.")

    return latitude, longitude


# Файл: main.py
# (ВСТАВИТЬ ВМЕСТО ВСЕЙ ФУНКЦИИ run_fuzzy_logic)
# (ВЕРСИЯ 4.1 - "Патч" 7.1. "Чинит" 'MarkupError [//]')

def run_fuzzy_logic(raw_data: dict, source_name: str = "API"):
    """
    (ФИНАЛЬНАЯ "ДОЛИЗАННАЯ" ВЕРСИЯ v4.2)
    Запускает ВЕСЬ "матан" (Система А + Система Б).
    "Возвращает" "секси" 'Panel' для *каждого* "движка".
    """
    console.log("[bold magenta]--- ЗАПУСК 'МАТАНА' (Fuzzy Engine) ---[/]")
    console.log(f"[grey50]Источник данных: {source_name}[/grey50]")
    
    current_data = raw_data.get('current', {})
    hourly_data = raw_data.get('hourly', {})
    
    if not current_data:
        console.log("[bold red]Ошибка: 'current' данные отсутствуют. 'Мгновенный' матан отменен.[/]")
        return
        
    # "Контейнеры" (Чинит 'UnboundLocalError')
    particle_risk_result = None
    gas_risk_result = None
    other_risk_result = None
    final_aqi_score = None
    final_recommendation_index = None
    forecast_text = "N/A (Прогноз не запущен)"

    # --- 1. ПОД-СИСТЕМА "ЧАСТИЦЫ" (Мгновенный) ---
    console.log("[cyan]... Инициализация Под-системы 'Частицы' ...[/]")
    try:
        particle_engine_ctrl = create_particle_engine()
        particle_simulation = ctrl.ControlSystemSimulation(particle_engine_ctrl)
        
        input_pm2_5 = current_data.get('pm2_5', 0) or 0
        input_pm10 = current_data.get('pm10', 0) or 0
        input_aod = current_data.get('aerosol_optical_depth', 0) or 0
        input_dust = current_data.get('dust', 0) or 0
        
        particle_simulation.input['pm2_5'] = input_pm2_5
        particle_simulation.input['pm10'] = input_pm10
        particle_simulation.input['aod'] = input_aod
        particle_simulation.input['dust'] = input_dust

        particle_simulation.compute()
        particle_risk_result = particle_simulation.output['Particle_Risk']
        
        console.log("[bold green]ПОД-СИСТЕМА 'ЧАСТИЦЫ' ОТРАБОТАЛА:[/]")
        console.print(Panel(
            f"Входы: [ PM2.5: {input_pm2_5}, PM10: {input_pm10}, AOD: {input_aod}, Dust: {input_dust} ]\n"
            f"Выход (0-100): [bold yellow]Particle_Risk = {particle_risk_result:.2f}[/bold yellow]",
            title="[green]Результат 1 (Дефаззификация)[/green]"
        ))
    except Exception as e:
        console.log("[bold red]КРИТИЧЕСКАЯ ОШИБКА ('Частицы'):[/]")
        console.print_exception()

    # --- 2. ПОД-СИСТЕМА "ГАЗЫ" (Мгновенный) ---
    console.log("[cyan]... Инициализация Под-системы 'Газы' ...[/]")
    try:
        gas_engine_ctrl = create_gas_engine()
        gas_simulation = ctrl.ControlSystemSimulation(gas_engine_ctrl)
        
        input_co = current_data.get('carbon_monoxide', 0) or 0
        input_no2 = current_data.get('nitrogen_dioxide', 0) or 0
        input_so2 = current_data.get('sulphur_dioxide', 0) or 0
        
        gas_simulation.input['co'] = input_co
        gas_simulation.input['no2'] = input_no2
        gas_simulation.input['so2'] = input_so2
        
        gas_simulation.compute()
        gas_risk_result = gas_simulation.output['Gas_Risk']
        
        console.log("[bold green]ПОД-СИСТЕМА 'ГАЗЫ' ОТРАБОТАЛА:[/]")
        console.print(Panel(
            f"Входы: [ CO: {input_co}, NO2: {input_no2}, SO2: {input_so2} ]\n"
            f"Выход (0-100): [bold yellow]Gas_Risk = {gas_risk_result:.2f}[/bold yellow]",
            title="[green]Результат 2 (Дефаззификация)[/green]"
        ))
    except Exception as e:
        console.log("[bold red]КРИТИЧЕСКАЯ ОШИБКА ('Газы'):[/]")
        console.print_exception()

    # --- 3. ПОД-СИСТЕМА "ПРОЧИЕ" (Мгновенный) ---
    console.log("[cyan]... Инициализация Под-системы 'Прочие' ...[/]")
    try:
        other_engine_ctrl = create_other_engine()
        other_simulation = ctrl.ControlSystemSimulation(other_engine_ctrl)
        
        input_o3 = current_data.get('ozone', 0) or 0
        input_nh3 = current_data.get('ammonia', 0) or 0
        
        other_simulation.input['o3'] = input_o3
        other_simulation.input['nh3'] = input_nh3

        other_simulation.compute()
        other_risk_result = other_simulation.output['Other_Risk']
        
        console.log("[bold green]ПОД-СИСТЕМА 'ПРОЧИЕ' ОТРАБОТАЛА:[/]")
        console.print(Panel(
            f"Входы: [ O3: {input_o3}, NH3: {input_nh3} ]\n"
            f"Выход (0-100): [bold yellow]Other_Risk = {other_risk_result:.2f}[/bold yellow]",
            title="[green]Результат 3 (Дефаззификация)[/green]"
        ))
    except Exception as e:
        console.log("[bold red]КРИТИЧЕСКАЯ ОШИБКА ('Прочие'):[/]")
        console.print_exception()


    # --- 4. "МАСТЕР-СИСТЕМА" (Мгновенный) ---
    console.log("[bold magenta]... Инициализация ГЛАВНОЙ (Мастер) Системы ...[/]")
    
    # "Секси" текст для "Мгновенного" AQI (Инициализируем ДО "try/except")
    rec_text = "N/A (Ошибка 'Мастера')"
    
    if (particle_risk_result is not None and 
        gas_risk_result is not None and 
        other_risk_result is not None):
        
        try:
            master_engine_ctrl = create_master_engine()
            master_simulation = ctrl.ControlSystemSimulation(master_engine_ctrl)
            
            master_simulation.input['particle_risk_in'] = particle_risk_result
            master_simulation.input['gas_risk_in'] = gas_risk_result
            master_simulation.input['other_risk_in'] = other_risk_result
            
            master_simulation.compute()

            final_aqi_score = master_simulation.output['Final_AQI']
            final_recommendation_index = master_simulation.output['Recommendation']
            
            # --- "ВОЗВРАЩАЕМ" "ТВОЙ" 'Panel' (Из "старого" кода v3.1.1) ---
            if final_recommendation_index <= 3: # stay_home
                rec_text = "[bold white on red]ОСТАВАЙТЕСЬ ДОМА[/]: Экстремально опасно."
            elif final_recommendation_index <= 6.5: # limit_activity
                rec_text = "[bold yellow]ОГРАНИЧЬТЕ АКТИВНОСТЬ[/]: Нездорово."
            elif final_recommendation_index <= 9: # go_out_safe
                rec_text = "[bold green]ПРОГУЛКИ БЕЗОПАСНЫ[/]: Качество приемлемое."
            else: # perfect_day
                rec_text = "[bold cyan]ИДЕАЛЬНЫЙ ДЕНЬ[/]: Воздух чистый."

            console.log("[bold yellow]=== ФИНАЛЬНЫЙ ВЕРДИКТ СИСТЕМЫ (A) ===[/]")
            console.print(Panel(
                f"Входы: [ P_Risk: {particle_risk_result:.2f}, G_Risk: {gas_risk_result:.2f}, O_Risk: {other_risk_result:.2f} ]\n\n"
                f"Финальный AQI (0-500): [bold white on red] {final_aqi_score:.2f} [/]\n"
                f"Рекомендация: {rec_text}",
                title="[yellow bold]Мастер-Система (Дефаззификация)[/]"
            ))
            # --- "ПАТЧ" (Возвращение "старого" 'Panel') ОКОНЧЕН ---

        except Exception as e:
            console.log("[bold red]КРИТИЧЕСКАЯ ОШИБКА ('Мастер-Система'):[/]")
            console.print_exception()
    
    else:
        console.log("[bold red]Ошибка: Недостаточно данных от под-систем для запуска 'Мастер-Системы'[/]")

    
    # --- 5. "ПРОГНОЗНЫЙ ДВИЖОК" (Система Б) ---
    console.log("[bold blue]--- ЗАПУСК 'СИСТЕМЫ Б' (Прогноз 24ч) ---[/]")
    
    if not hourly_data or 'pm2_5' not in hourly_data or not hourly_data['pm2_5']:
        console.log("[bold red]Ошибка: 'hourly' данные отсутствуют. 'Прогнозный' матан отменен.[/]")
        forecast_text = "N/A (Нет 'hourly' данных)"
    
    else:
        try:
            forecast_inputs = preprocess_hourly_data(hourly_data, hours_to_forecast=24)
            
            if forecast_inputs:
                forecast_engine_ctrl = create_forecast_engine()
                forecast_simulation = ctrl.ControlSystemSimulation(forecast_engine_ctrl)
                
                forecast_simulation.input['pm_avg'] = forecast_inputs.get('pm_avg', 0)
                forecast_simulation.input['pm_max'] = forecast_inputs.get('pm_max', 0)
                forecast_simulation.input['pm_hours_bad'] = forecast_inputs.get('pm_hours_bad', 0)
                forecast_simulation.input['gas_norm_risk'] = forecast_inputs.get('gas_norm_risk', 0)
                forecast_simulation.input['o3_max'] = forecast_inputs.get('o3_max', 0)

                forecast_simulation.compute()
                forecast_risk_score = forecast_simulation.output['Forecast_Risk']
                
                peak_time_text = ""
                if forecast_risk_score > 30: 
                    peak_hour = forecast_inputs.get('pm_peak_hour', -1)
                    if 5 <= peak_hour < 12:
                        peak_time_text = "[bold](Пик PM2.5 ожидается УТРОМ)[/bold]"
                    elif 12 <= peak_hour < 18:
                        peak_time_text = "[bold](Пик PM2.5 ожидается ДНЕМ)[/bold]"
                    elif 18 <= peak_hour <= 23:
                        peak_time_text = "[bold](Пик PM2.5 ожидается ВЕЧЕРОМ)[/bold]"
                    elif 0 <= peak_hour < 5:
                        peak_time_text = "[bold](Пик PM2.5 ожидается НОЧЬЮ)[/bold]"

                if forecast_risk_score <= 30: # low
                    forecast_text = f"[bold green]НИЗКИЙ РИСК[/]: Прогноз на 24ч стабильный."
                elif forecast_risk_score <= 65: # medium
                    forecast_text = f"[bold yellow]СРЕДНИЙ РИСК[/]: Будьте осторожны. {peak_time_text}"
                else: # high / critical
                    forecast_text = f"[bold red]ВЫСОКИЙ РИСК[/]: 'Грязный' день. {peak_time_text}"

                # --- "ВОЗВРАЩАЕМ" "СЕКСИ" 'Panel' ДЛЯ "СИСТЕМЫ Б" ---
                console.log("[bold blue]ПРОГНОЗНЫЙ ДВИЖОК ОТРАБОТАЛ:[/]")
                console.print(Panel(
                    f"Входы (статистика 24ч): [ PM_Avg: {forecast_inputs.get('pm_avg'):.2f}, PM_Max: {forecast_inputs.get('pm_max'):.2f}, PM_Hours_Bad: {forecast_inputs.get('pm_hours_bad')} ]\n"
                    f"Входы (статистика 24ч): [ Gas_Norm_Risk: {forecast_inputs.get('gas_norm_risk'):.2f}, O3_Max: {forecast_inputs.get('o3_max'):.2f} ]\n\n"
                    f"Выход (0-100): [bold yellow]Forecast_Risk = {forecast_risk_score:.2f}[/bold yellow]\n"
                    f"Вердикт на 24ч: {forecast_text}",
                    title="[blue]Результат 'Системы Б' (Прогноз v2.0)[/]"
                ))

        except Exception as e:
            console.log("[bold red]КРИТИЧЕСКАЯ ОШИБКА ('Прогнозный Движок'):[/]")
            console.print_exception()


    # --- "ХОТФИКС" (v4.2): "Чиним" "контейнеры" для "Сводки" ---
    if final_aqi_score is None or final_recommendation_index is None:
        rec_text = "[bold red]ОШИБКА 'Мастера'[/]"
        final_aqi_score = 0.0
    
    # --- ФИНАЛЬНЫЙ ВЫВОД (Сводка) ---
    console.log("[bold yellow]=== ФИНАЛЬНЫЙ ВЕРДИКТ (Сводка) ===[/]")
    console.print(Panel(
        f"СЕЙЧАС (Система А):  [bold]{final_aqi_score:.2f}[/] AQI | {rec_text}\n"
        f"ПРОГНОЗ (Система Б): {forecast_text}",
        title="[yellow bold]Fuzzy Atmosphere Engine (Вердикт)[/]"
    ))

    # --- "СЖИГАЕМ" JUPYTER ---
    console.log("[bold grey50]... 'Матан' завершен ...[/]")
    # -------------------------
    
def run_live_mode():
    """
    (Этап 1.2) Запускаем "боевой" режим парсинга.
    """
    latitude, longitude = get_coordinates()
    console.log(f"Координаты приняты: ({latitude}, {longitude}). Запускаем парсер...")
    
    client = AirQualityClient()
    raw_data = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=True 
    ) as progress:
        
        task_current = progress.add_task("[cyan]Парсинг 'Current' (9+2)...[/cyan]", total=100)
        task_hourly = progress.add_task("[blue]Парсинг 'Hourly' (Массивы)...[/blue]", total=100)

        time.sleep(0.5)
        
        try:
            raw_data = client.get_air_quality(latitude, longitude)
            
            progress.update(task_current, completed=100, description="[green]Парсинг 'Current' (9+2) [bold]OK[/bold][/green]")
            time.sleep(0.3)
            progress.update(task_hourly, completed=100, description="[green]Парсинг 'Hourly' (Массивы) [bold]OK[/bold][/green]")
            time.sleep(0.5)

        except Exception as e:
            progress.stop()
            console.log(f"[bold red]КРИТИЧЕСКАЯ ОШИБКА API:[/]")
            console.print_exception()
            return

    console.log("[bold green]Парсинг прошел успешно![/]")
    
    current_data_clean = raw_data.get('current', {})
    filtered_current = {
        key: current_data_clean.get(key) for key in CURRENT_PARAMS 
        if key in current_data_clean
    }
    console.print(Pretty(filtered_current))
    
    hourly_data = raw_data.get('hourly', {})
    if 'time' in hourly_data and hourly_data.get('pm2_5'):
        timestamps_count = len(hourly_data['time'])
        console.log(f"[bold]Парсинг 'Hourly' массивов получен.[/] [grey50]({timestamps_count} таймстэмпов)[/grey50]")
    else:
        console.log("[yellow]Внимание: 'Hourly' данные не получены (пустой ответ).[/yellow]")

    if raw_data:
        run_fuzzy_logic(raw_data, source_name=f"API: ({latitude}, {longitude})")
    else:
        console.log("[bold red]Нет 'сырых' данных для 'матана'.[/]")


def run_mock_mode():
    """
    (Этап 5 - "Хардтест") Запускаем режим генерации.
    Читает "жопу" из 'mock_data.json'.
    """
    console.log("[bold yellow]Режим 'Тестовый' (Mock)[/]")
    MOCK_FILE = "mock_data.json"
    
    try:
        with open(MOCK_FILE, 'r', encoding='utf-8') as f:
            mock_scenarios = json.load(f)
        
        console.print("Доступные 'хардтест' сценарии из [cyan]mock_data.json[/cyan]:")
        
        scenario_keys = list(mock_scenarios.keys())
        prompt_text = "\n"
        choices = []
        for i, key in enumerate(scenario_keys):
            comment = mock_scenarios[key].get('comment', 'N/A')
            prompt_text += f"  [{i+1}] {key} ([grey50]{comment}[/grey50])\n"
            choices.append(str(i+1))
        
        prompt_text += "\n  [q] Назад в Главное Меню\n\n  Ваш выбор:"
        choices.append("q")

        choice = Prompt.ask(prompt_text, choices=choices, default="1")
        
        if choice == 'q':
            return
            
        selected_key = scenario_keys[int(choice)-1]
        console.log(f"Загружаем сценарий: [bold yellow]{selected_key}[/]")
        
        mock_raw_data = mock_scenarios[selected_key]
        
        run_fuzzy_logic(mock_raw_data, source_name=f"Mock: {selected_key}")

    except FileNotFoundError:
        console.log(f"[bold red]Критическая Ошибка: Файл '{MOCK_FILE}' не найден![/]")
        console.log("Пожалуйста, создайте 'mock_data.json' в корневой папке.")
    except Exception as e:
        console.log("[bold red]Критическая Ошибка в 'Тестовом режиме':[/]")
        console.print_exception()


def main():
    """
    (Этап 0) Главный цикл программы.
    """
    print_autograph()
    
    while True:
        console.print(Panel(
            "Выберите режим работы:",
            title="[cyan]Главное Меню[/]",
            padding=(1, 2)
        ))
        
        mode = Prompt.ask(
            "  [1] 'Живой' режим (Парсинг API по координатам)\n"
            "  [2] 'Тестовый' режим (Генерация данных)\n"
            "  [q] Выход\n"
            "\n  Ваш выбор:",
            choices=["1", "2", "q"],
            default="1"
        )
        
        if mode == '1':
            run_live_mode()
        elif mode == '2':
            run_mock_mode()
        elif mode == 'q':
            console.log("[bold yellow]Выход. Спим довольные.[/]")
            break
        
        console.print("\n" + "="*80 + "\n") # Разделитель

if __name__ == "__main__":
    main()