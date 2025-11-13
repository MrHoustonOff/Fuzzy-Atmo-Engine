"""
Главный исполняемый файл приложения Fuzzy Atmo-Engine.

Отвечает за основной цикл работы, взаимодействие с пользователем через
консольное меню, запуск выбранного режима (получение данных из API
или использование тестовых сценариев) и вызов системы нечеткой логики
для анализа полученных данных.
"""
import time
import json
from rich.panel import Panel
from rich.prompt import Prompt
from rich.pretty import Pretty
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
import skfuzzy.control as ctrl

from src.utils.logger import console
from src.api_client.client import AirQualityClient
from config import CURRENT_PARAMS

# Импорты движков нечеткой логики
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


def get_coordinates() -> tuple[float, float]:
    """
    Запрашивает у пользователя ввод географических координат.

    Выполняет валидацию введенных данных, чтобы широта находилась
    в диапазоне [-90, 90], а долгота - в [-180, 180].

    Returns:
        tuple[float, float]: Кортеж, содержащий широту и долготу.
    """
    console.print(Panel.fit(
        "Для получения данных о качестве воздуха необходимы координаты.\n"
        "Вы можете определить их по ссылке: [bold link=https://www.latlong.net/]https://www.latlong.net/[/]",
        title="[yellow]Ввод данных[/yellow]",
        padding=(1, 2)
    ))

    while True:
        try:
            lat_str = Prompt.ask("   [cyan]Введите широту (Latitude)[/cyan]")
            latitude = float(lat_str)
            if not -90 <= latitude <= 90:
                raise ValueError("Широта должна быть в диапазоне от -90 до 90.")
            break
        except ValueError as e:
            console.print(f"[bold red]Ошибка ввода![/] {e} Попробуйте еще раз.")

    while True:
        try:
            lon_str = Prompt.ask("   [cyan]Введите долготу (Longitude)[/cyan]")
            longitude = float(lon_str)
            if not -180 <= longitude <= 180:
                raise ValueError("Долгота должна быть в диапазоне от -180 до 180.")
            break
        except ValueError as e:
            console.print(f"[bold red]Ошибка ввода![/] {e} Попробуйте еще раз.")

    return latitude, longitude


def run_fuzzy_logic(raw_data: dict, source_name: str = "API"):
    """
    Запускает полный цикл расчетов системы нечеткой логики.

    Последовательно выполняет расчеты для всех подсистем (частицы, газы,
    прочие), агрегирует их результаты в Мастер-системе для получения
    текущего AQI, а затем запускает прогнозную систему на 24 часа.

    Args:
        raw_data (dict): Словарь с "сырыми" данными от API, содержащий
                         ключи 'current' и 'hourly'.
        source_name (str): Строка, описывающая источник данных
                           (например, "API" или название mock-сценария).
    """
    console.log("[bold magenta]--- ЗАПУСК СИСТЕМЫ НЕЧЕТКОЙ ЛОГИКИ ---[/]")
    console.log(f"[grey50]Источник данных: {source_name}[/grey50]")

    current_data = raw_data.get('current', {})
    hourly_data = raw_data.get('hourly', {})

    if not current_data:
        console.log("[bold red]Ошибка: отсутствуют данные 'current'. Расчет текущих показателей отменен.[/]")
        return

    # Инициализация переменных для хранения результатов
    particle_risk_result = None
    gas_risk_result = None
    other_risk_result = None
    final_aqi_score = None
    forecast_text = "Прогноз не выполнен (отсутствуют данные)"

    # --- 1. Подсистема "Частицы" ---
    console.log("\n[cyan]1. Расчет риска: Подсистема 'Частицы'[/]")
    try:
        particle_engine_ctrl = create_particle_engine()
        particle_simulation = ctrl.ControlSystemSimulation(particle_engine_ctrl)
        
        # 📌 ИСПРАВЛЕНИЕ: Сохраняем в переменные для последующего вывода
        input_pm2_5 = current_data.get('pm2_5', 0) or 0
        input_pm10 = current_data.get('pm10', 0) or 0
        input_aod = current_data.get('aerosol_optical_depth', 0) or 0
        input_dust = current_data.get('dust', 0) or 0

        # Установка входных значений
        particle_simulation.input['pm2_5'] = input_pm2_5
        particle_simulation.input['pm10'] = input_pm10
        particle_simulation.input['aod'] = input_aod
        particle_simulation.input['dust'] = input_dust

        particle_simulation.compute()
        particle_risk_result = particle_simulation.output['Particle_Risk']
        
        console.print(Panel(
            # 📌 ИСПРАВЛЕНИЕ: Читаем из переменных
            f"Входы: [ PM2.5: {input_pm2_5:.2f}, PM10: {input_pm10:.2f}, "
            f"AOD: {input_aod:.2f}, Dust: {input_dust:.2f} ]\n"
            f"Выходной риск (0-100): [bold yellow]{particle_risk_result:.2f}[/]",
            title="[green]Подсистема 'Частицы': Результат[/green]"
        ))
    except Exception:
        console.log("[bold red]Критическая ошибка в подсистеме 'Частицы':[/]")
        console.print_exception()

    # --- 2. Подсистема "Газы" ---
    console.log("\n[cyan]2. Расчет риска: Подсистема 'Газы'[/]")
    try:
        gas_engine_ctrl = create_gas_engine()
        gas_simulation = ctrl.ControlSystemSimulation(gas_engine_ctrl)
        
        # 📌 ИСПРАВЛЕНИЕ: Сохраняем в переменные для последующего вывода
        input_co = current_data.get('carbon_monoxide', 0) or 0
        input_no2 = current_data.get('nitrogen_dioxide', 0) or 0
        input_so2 = current_data.get('sulphur_dioxide', 0) or 0
        
        # Установка входных значений
        gas_simulation.input['co'] = input_co
        gas_simulation.input['no2'] = input_no2
        gas_simulation.input['so2'] = input_so2
        
        gas_simulation.compute()
        gas_risk_result = gas_simulation.output['Gas_Risk']
        
        console.print(Panel(
            # 📌 ИСПРАВЛЕНИЕ: Читаем из переменных
            f"Входы: [ CO: {input_co:.2f}, NO2: {input_no2:.2f}, SO2: {input_so2:.2f} ]\n"
            f"Выходной риск (0-100): [bold yellow]{gas_risk_result:.2f}[/]",
            title="[green]Подсистема 'Газы': Результат[/green]"
        ))
    except Exception:
        console.log("[bold red]Критическая ошибка в подсистеме 'Газы':[/]")
        console.print_exception()

    # --- 3. Подсистема "Прочие" ---
    console.log("\n[cyan]3. Расчет риска: Подсистема 'Прочие'[/]")
    try:
        other_engine_ctrl = create_other_engine()
        other_simulation = ctrl.ControlSystemSimulation(other_engine_ctrl)

        # 📌 ИСПРАВЛЕНИЕ: Сохраняем в переменные для последующего вывода
        input_o3 = current_data.get('ozone', 0) or 0
        input_nh3 = current_data.get('ammonia', 0) or 0
        
        # Установка входных значений
        other_simulation.input['o3'] = input_o3
        other_simulation.input['nh3'] = input_nh3

        other_simulation.compute()
        other_risk_result = other_simulation.output['Other_Risk']
        
        console.print(Panel(
            # 📌 ИСПРАВЛЕНИЕ: Читаем из переменных
            f"Входы: [ O3: {input_o3:.2f}, NH3: {input_nh3:.2f} ]\n"
            f"Выходной риск (0-100): [bold yellow]{other_risk_result:.2f}[/]",
            title="[green]Подсистема 'Прочие': Результат[/green]"
        ))
    except Exception:
        console.log("[bold red]Критическая ошибка в подсистеме 'Прочие':[/]")
        console.print_exception()

    # --- 4. Мастер-система (агрегация результатов) ---
    console.log("\n[bold magenta]4. Агрегация: Мастер-система (Текущий AQI)[/]")
    rec_text = "Ошибка при вычислении рекомендации"
    
    if all(r is not None for r in [particle_risk_result, gas_risk_result, other_risk_result]):
        try:
            master_engine_ctrl = create_master_engine()
            master_simulation = ctrl.ControlSystemSimulation(master_engine_ctrl)
            
            master_simulation.input['particle_risk_in'] = particle_risk_result
            master_simulation.input['gas_risk_in'] = gas_risk_result
            master_simulation.input['other_risk_in'] = other_risk_result
            
            master_simulation.compute()

            final_aqi_score = master_simulation.output['Final_AQI']
            recommendation_index = master_simulation.output['Recommendation']
            
            if recommendation_index <= 3:
                rec_text = "[bold white on red]ОЧЕНЬ ВЫСОКИЙ РИСК[/]: Оставайтесь в помещении."
            elif recommendation_index <= 6.5:
                rec_text = "[bold yellow]ПОВЫШЕННЫЙ РИСК[/]: Ограничьте активность на улице."
            elif recommendation_index <= 9:
                rec_text = "[bold green]УМЕРЕННЫЙ РИСК[/]: Прогулки безопасны."
            else:
                rec_text = "[bold cyan]НИЗКИЙ РИСК[/]: Отличный день для прогулки!"

            console.print(Panel(
                f"Входные риски: [ Частицы: {particle_risk_result:.2f}, Газы: {gas_risk_result:.2f}, Прочие: {other_risk_result:.2f} ]\n\n"
                f"Итоговый AQI (0-500): [bold white on red] {final_aqi_score:.2f} [/]\n"
                f"Рекомендация: {rec_text}",
                title="[bold yellow]Мастер-система: Текущая оценка AQI[/]"
            ))
        except Exception:
            console.log("[bold red]Критическая ошибка в Мастер-системе:[/]")
            console.print_exception()
    else:
        console.log("[bold red]Ошибка: Недостаточно данных от подсистем для запуска Мастер-системы.[/]")

    # --- 5. Прогнозная система ---
    console.log("\n[bold blue]--- ЗАПУСК ПРОГНОЗНОЙ СИСТЕМЫ (24 ЧАСА) ---[/]")
    if not hourly_data or 'pm2_5' not in hourly_data or not hourly_data['pm2_5']:
        console.log("[yellow]Предупреждение: Отсутствуют почасовые данные. Расчет прогноза отменен.[/yellow]")
    else:
        try:
            forecast_inputs = preprocess_hourly_data(hourly_data, hours_to_forecast=24)
            if forecast_inputs:
                forecast_engine_ctrl = create_forecast_engine()
                forecast_simulation = ctrl.ControlSystemSimulation(forecast_engine_ctrl)
                
                # Передача вычисленных статистик в движок
                for key, value in forecast_inputs.items():
                    # 📌 ИСПРАВЛЕНИЕ: Используем .ctrl.input для проверки, поддерживает итерацию
                    if key in forecast_simulation.ctrl.input:
                        forecast_simulation.input[key] = value

                forecast_simulation.compute()
                forecast_risk_score = forecast_simulation.output['Forecast_Risk']
                
                peak_time_text = ""
                if forecast_risk_score > 30: 
                    peak_hour = forecast_inputs.get('pm_peak_hour', -1)
                    if 5 <= peak_hour < 12:   peak_time_text = "[bold](Пик загрязнения ожидается утром)[/]"
                    elif 12 <= peak_hour < 18:   peak_time_text = "[bold](Пик загрязнения ожидается днем)[/]"
                    elif 18 <= peak_hour <= 23: peak_time_text = "[bold](Пик загрязнения ожидается вечером)[/]"
                    elif 0 <= peak_hour < 5:    peak_time_text = "[bold](Пик загрязнения ожидается ночью)[/]"

                if forecast_risk_score <= 30:
                    forecast_text = f"[bold green]НИЗКИЙ РИСК[/]: Прогноз на 24ч стабильный."
                elif forecast_risk_score <= 65:
                    forecast_text = f"[bold yellow]СРЕДНИЙ РИСК[/]: Рекомендуется осторожность. {peak_time_text}"
                else:
                    forecast_text = f"[bold red]ВЫСОКИЙ РИСК[/]: Возможен неблагоприятный день. {peak_time_text}"

                console.print(Panel(
                    f"Выходной риск (0-100): [bold yellow]{forecast_risk_score:.2f}[/]\n"
                    f"Прогноз на 24 часа: {forecast_text}",
                    title="[bold blue]Прогнозная система: Результат на 24 часа[/]"
                ))
        except Exception:
            console.log("[bold red]Критическая ошибка в Прогнозной системе:[/]")
            console.print_exception()

    # --- Итоговый отчет ---
    if final_aqi_score is None:
        final_aqi_score = 0.0   # Установка значения по умолчанию для вывода
        rec_text = "[red]не рассчитан[/]"

    console.print(Panel(
        f"[b]Текущая оценка:[/b] {final_aqi_score:.2f} AQI | {rec_text}\n"
        f"[b]Прогноз на 24ч:[/b]  {forecast_text}",
        title="[bold yellow]Сводный отчет: Fuzzy Atmo-Engine[/]",
        padding=(1,2)
    ))
    console.log("[bold grey50]... Расчеты системы нечеткой логики завершены ...[/]")


def run_live_mode():
    """Запускает "живой" режим с получением данных из API по координатам."""
    latitude, longitude = get_coordinates()
    console.log(f"Координаты приняты: ({latitude}, {longitude}). Запрос данных из API...")
    
    client = AirQualityClient()
    raw_data = None

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console, transient=True 
    ) as progress:
        task_current = progress.add_task("[cyan]Запрос текущих данных...[/]", total=100)
        task_hourly = progress.add_task("[blue]Запрос прогноза...[/]", total=100)
        time.sleep(0.5)
        
        try:
            raw_data = client.get_air_quality(latitude, longitude)
            progress.update(task_current, completed=100, description="[green]Текущие данные получены [bold]OK[/]")
            time.sleep(0.3)
            progress.update(task_hourly, completed=100, description="[green]Данные прогноза получены [bold]OK[/]")
            time.sleep(0.5)
        except Exception:
            progress.stop()
            console.log(f"[bold red]КРИТИЧЕСКАЯ ОШИБКА API:[/]")
            console.print_exception()
            return

    console.log("[bold green]Данные из API успешно получены![/]")
    current_data = raw_data.get('current', {})
    filtered_current = {
        key: current_data.get(key) for key in CURRENT_PARAMS if key in current_data
    }
    console.print(Panel(Pretty(filtered_current), title="[bold]Текущие показатели[/]"))
    
    if 'time' in raw_data.get('hourly', {}):
        count = len(raw_data['hourly']['time'])
        console.log(f"[bold]Получены почасовые данные для прогноза.[/] [grey50]({count} записей)[/grey50]")
    else:
        console.log("[yellow]Внимание: почасовые данные для прогноза не получены.[/yellow]")

    if raw_data:
        run_fuzzy_logic(raw_data, source_name=f"API: ({latitude}, {longitude})")
    else:
        console.log("[bold red]Нет данных для запуска системы логики.[/]")


def run_mock_mode():
    """Запускает тестовый режим с использованием данных из `mock_data.json`."""
    console.log("\n[bold yellow]Запуск в тестовом режиме (из mock_data.json)[/]")
    MOCK_FILE = "mock_data.json"
    
    try:
        with open(MOCK_FILE, 'r', encoding='utf-8') as f:
            mock_scenarios = json.load(f)
        
        console.print("Доступные тестовые сценарии из [cyan]mock_data.json[/cyan]:")
        scenario_keys = list(mock_scenarios.keys())
        prompt_text = "\n"
        choices = []
        for i, key in enumerate(scenario_keys):
            comment = mock_scenarios[key].get('comment', 'Нет описания')
            prompt_text += f"   [{i+1}] {key} ([grey50]{comment}[/grey50])\n"
            choices.append(str(i+1))
        
        prompt_text += "\n   [q] Назад в Главное Меню\n\n   Выберите сценарий:"
        choices.append("q")
        choice = Prompt.ask(prompt_text, choices=choices, default="1")
        
        if choice == 'q': return
            
        selected_key = scenario_keys[int(choice)-1]
        console.log(f"Загрузка сценария: [bold yellow]{selected_key}[/]")
        run_fuzzy_logic(mock_scenarios[selected_key], source_name=f"Mock: {selected_key}")

    except FileNotFoundError:
        console.log(f"[bold red]Критическая Ошибка: Файл '{MOCK_FILE}' не найден![/]")
    except Exception:
        console.log("[bold red]Критическая Ошибка в тестовом режиме:[/]")
        console.print_exception()


def main():
    """Главная функция, запускающая основной цикл программы."""
    print_autograph()
    
    while True:
        console.print(Panel(
            "Выберите режим работы:",
            title="[cyan]Главное Меню[/]",
            padding=(1, 2)
        ))
        mode = Prompt.ask(
            "   [1] 'Живой' режим (данные из API по координатам)\n"
            "   [2] 'Тестовый' режим (данные из файла)\n"
            "   [q] Выход\n"
            "\n   Ваш выбор:",
            choices=["1", "2", "q"], default="1"
        )
        
        if mode == '1': run_live_mode()
        elif mode == '2': run_mock_mode()
        elif mode == 'q':
            console.log("[bold yellow]Завершение работы программы.[/]")
            break
        
        Prompt.ask("\n[bold]Нажмите Enter, чтобы вернуться в Главное Меню...[/]")
        console.print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()