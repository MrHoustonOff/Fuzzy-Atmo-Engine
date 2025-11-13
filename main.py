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
# --- НОВОЕ: Импортируем настройки для графиков ---
from config import CURRENT_PARAMS, CREATE_GRAPHICS, GRAPHICS_OUTPUT_DIR
# --- НОВОЕ: Импортируем наш менеджер графиков ---
try:
    from src.utils.graphics_manager import GraphicsManager
except ImportError:
    GraphicsManager = None
    if CREATE_GRAPHICS:
        console.log("[bold red]Ошибка: Не удалось импортировать GraphicsManager. Убедитесь, что `matplotlib` и `pillow` установлены.[/]")


# Импорты движков нечеткой логики
from src.fuzzy_engine.particle_subsystem import create_particle_engine
from src.fuzzy_engine.gas_subsystem import create_gas_engine
from src.fuzzy_engine.other_subsystem import create_other_engine
from src.fuzzy_engine.master_system import create_master_engine
from src.fuzzy_engine.forecast_preprocessor import preprocess_hourly_data
from src.fuzzy_engine.forecast_system import create_forecast_engine


def print_autograph():
    """Выводит в консоль стилизованный ASCII-арт автограф."""
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
    """Запрашивает у пользователя ввод географических координат."""
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


def run_fuzzy_logic(raw_data: dict, source_name: str = "API", manager: GraphicsManager | None = None):
    """
    Запускает полный цикл расчетов системы нечеткой логики.
    """
    console.log("[bold magenta]--- ЗАПУСК СИСТЕМЫ НЕЧЕТКОЙ ЛОГИКИ ---[/]")
    console.log(f"[grey50]Источник данных: {source_name}[/grey50]")

    current_data = raw_data.get('current', {})
    hourly_data = raw_data.get('hourly', {})

    if not current_data:
        console.log("[bold red]Ошибка: отсутствуют данные 'current'. Расчет отменен.[/]")
        return

    # --- ИСПРАВЛЕНИЕ: Инициализируем ВСЕ переменные здесь ---
    particle_risk_result = None
    gas_risk_result = None
    other_risk_result = None
    final_aqi_score = None
    rec_text = "N/A" # Значение по умолчанию
    forecast_text = "Прогноз не выполнен (ошибка в предыдущих шагах)" # Значение по умолчанию
    
    # --- 1. Подсистема "Частицы" ---
    console.log("\n[cyan]1. Расчет риска: Подсистема 'Частицы'[/]")
    try:
        particle_engine_ctrl = create_particle_engine()
        antecedent_vars = {var.label: var for var in particle_engine_ctrl.antecedents}
        consequent_var = {var.label: var for var in particle_engine_ctrl.consequents}['Particle_Risk']
        particle_simulation = ctrl.ControlSystemSimulation(particle_engine_ctrl)
        
        inputs_values = {'pm2_5': current_data.get('pm2_5', 0) or 0, 'pm10': current_data.get('pm10', 0) or 0, 'aod': current_data.get('aerosol_optical_depth', 0) or 0, 'dust': current_data.get('dust', 0) or 0}
        for name, value in inputs_values.items():
            particle_simulation.input[name] = value
            if manager: manager.save_input_fuzzy_plot(antecedent_vars[name], value, f"Вход: {name.upper()} (Частицы)", f"01_input_particle_{name}.png")

        particle_simulation.compute()
        particle_risk_result = particle_simulation.output['Particle_Risk']
        
        if manager and particle_risk_result is not None:
            manager.save_output_fuzzy_plot(particle_simulation, consequent_var, "Выход: Риск от Частиц", "02_output_particle_risk.png")
        
        # --- ИСПРАВЛЕНИЕ: Возвращаем подробный вывод ---
        inputs_str = ', '.join([f"{k.upper()}: {v:.2f}" for k, v in inputs_values.items()])
        console.print(Panel(f"Входы: [ {inputs_str} ]\nВыходной риск (0-100): [bold yellow]{particle_risk_result:.2f}[/]", title="[green]Подсистема 'Частицы': Результат[/green]"))
    except Exception:
        console.log("[bold red]Критическая ошибка в подсистеме 'Частицы':[/]"); console.print_exception()

    # --- 2. Подсистема "Газы" ---
    console.log("\n[cyan]2. Расчет риска: Подсистема 'Газы'[/]")
    try:
        gas_engine_ctrl = create_gas_engine()
        antecedent_vars = {var.label: var for var in gas_engine_ctrl.antecedents}
        consequent_var = {var.label: var for var in gas_engine_ctrl.consequents}['Gas_Risk']
        gas_simulation = ctrl.ControlSystemSimulation(gas_engine_ctrl)
        
        inputs_values = {'co': current_data.get('carbon_monoxide', 0) or 0, 'no2': current_data.get('nitrogen_dioxide', 0) or 0, 'so2': current_data.get('sulphur_dioxide', 0) or 0}
        for name, value in inputs_values.items():
            gas_simulation.input[name] = value
            if manager: manager.save_input_fuzzy_plot(antecedent_vars[name], value, f"Вход: {name.upper()} (Газы)", f"03_input_gas_{name}.png")

        gas_simulation.compute()
        gas_risk_result = gas_simulation.output['Gas_Risk']
        
        if manager and gas_risk_result is not None:
            manager.save_output_fuzzy_plot(gas_simulation, consequent_var, "Выход: Риск от Газов", "04_output_gas_risk.png")

        inputs_str = ', '.join([f"{k.upper()}: {v:.2f}" for k, v in inputs_values.items()])
        console.print(Panel(f"Входы: [ {inputs_str} ]\nВыходной риск (0-100): [bold yellow]{gas_risk_result:.2f}[/]", title="[green]Подсистема 'Газы': Результат[/green]"))
    except Exception:
        console.log("[bold red]Критическая ошибка в подсистеме 'Газы':[/]"); console.print_exception()

    # --- 3. Подсистема "Прочие" ---
    console.log("\n[cyan]3. Расчет риска: Подсистема 'Прочие'[/]")
    try:
        other_engine_ctrl = create_other_engine()
        antecedent_vars = {var.label: var for var in other_engine_ctrl.antecedents}
        consequent_var = {var.label: var for var in other_engine_ctrl.consequents}['Other_Risk']
        other_simulation = ctrl.ControlSystemSimulation(other_engine_ctrl)

        inputs_values = {'o3': current_data.get('ozone', 0) or 0, 'nh3': current_data.get('ammonia', 0) or 0}
        for name, value in inputs_values.items():
            other_simulation.input[name] = value
            if manager: manager.save_input_fuzzy_plot(antecedent_vars[name], value, f"Вход: {name.upper()} (Прочие)", f"05_input_other_{name}.png")

        other_simulation.compute()
        other_risk_result = other_simulation.output['Other_Risk']
        
        if manager and other_risk_result is not None:
            manager.save_output_fuzzy_plot(other_simulation, consequent_var, "Выход: Риск от Прочих", "06_output_other_risk.png")

        inputs_str = ', '.join([f"{k.upper()}: {v:.2f}" for k, v in inputs_values.items()])
        console.print(Panel(f"Входы: [ {inputs_str} ]\nВыходной риск (0-100): [bold yellow]{other_risk_result:.2f}[/]", title="[green]Подсистема 'Прочие': Результат[/green]"))
    except Exception:
        console.log("[bold red]Критическая ошибка в подсистеме 'Прочие':[/]"); console.print_exception()


    # --- 4. Мастер-система (агрегация результатов) ---
    console.log("\n[bold magenta]4. Агрегация: Мастер-система (Текущий AQI)[/]")
    if all(r is not None for r in [particle_risk_result, gas_risk_result, other_risk_result]):
        try:
            master_engine_ctrl = create_master_engine()
            antecedent_vars = {var.label: var for var in master_engine_ctrl.antecedents}
            consequent_vars = {var.label: var for var in master_engine_ctrl.consequents}
            master_simulation = ctrl.ControlSystemSimulation(master_engine_ctrl)
            
            inputs_values = {'particle_risk_in': particle_risk_result, 'gas_risk_in': gas_risk_result, 'other_risk_in': other_risk_result}
            for name, value in inputs_values.items():
                master_simulation.input[name] = value
                if manager: manager.save_input_fuzzy_plot(antecedent_vars[name], value, f"Вход: {name} (Мастер)", f"07_input_master_{name}.png")

            master_simulation.compute()
            final_aqi_score = master_simulation.output['Final_AQI']
            recommendation_index = master_simulation.output['Recommendation']
            
            if manager:
                manager.save_output_fuzzy_plot(master_simulation, consequent_vars['Final_AQI'], "Выход: Финальный AQI (Мастер)", "08_output_master_aqi.png")
                manager.save_output_fuzzy_plot(master_simulation, consequent_vars['Recommendation'], "Выход: Рекомендация (Мастер)", "09_output_master_recommendation.png")
            
            if recommendation_index <= 3: rec_text = "[bold white on red]ОЧЕНЬ ВЫСОКИЙ РИСК[/]: Оставайтесь в помещении."
            elif recommendation_index <= 6.5: rec_text = "[bold yellow]ПОВЫШЕННЫЙ РИСК[/]: Ограничьте активность на улице."
            elif recommendation_index <= 9: rec_text = "[bold green]УМЕРЕННЫЙ РИСК[/]: Прогулки безопасны."
            else: rec_text = "[bold cyan]НИЗКИЙ РИСК[/]: Отличный день для прогулки!"

            inputs_str = ', '.join([f"{k}: {v:.2f}" for k, v in inputs_values.items()])
            console.print(Panel(f"Входы: [ {inputs_str} ]\n\nИтоговый AQI (0-500): [bold white on red] {final_aqi_score:.2f} [/]\nРекомендация: {rec_text}", title="[bold yellow]Мастер-система: Текущая оценка AQI[/]"))

        except Exception:
            console.log("[bold red]Критическая ошибка в Мастер-системе:[/]"); console.print_exception()
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
                
                # 📌📌📌 ФИКС СИСТЕМЫ ПРОГНОЗА (TypeError: not iterable):
                # Мы не можем проверять 'key in forecast_simulation.input'.
                # Мы должны проверять 'key' в списке имен из "шаблона".
                
                # 1. Получаем список имен входов из "шаблона"
                antecedent_labels = {var.label for var in forecast_engine_ctrl.antecedents}

                # 2. Передаем вычисленные статистики в движок
                for key, value in forecast_inputs.items():
                    if key in antecedent_labels: # 3. Проверяем по списку
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
        final_aqi_score, rec_text = 0.0, "[red]не рассчитан[/]"

    console.print(Panel(f"[b]Текущая оценка:[/b] {final_aqi_score:.2f} AQI | {rec_text}\n[b]Прогноз на 24ч:[/b]  {forecast_text}", title="[bold yellow]Сводный отчет: Fuzzy Atmo-Engine[/]", padding=(1,2)))
    
    if manager:
        pdf_title = f"Отчет_{source_name.replace(':', '_').replace(' ', '').replace('(', '').replace(')', '').replace(',', '')}"
        manager.generate_pdf_report(pdf_title)

    console.log("[bold grey50]... Расчеты системы нечеткой логики завершены ...[/]")


def run_live_mode():
    """Запускает "живой" режим с получением данных из API по координатам."""
    # --- НОВОЕ: Инициализация менеджера графиков ---
    manager = None
    if CREATE_GRAPHICS and GraphicsManager:
        console.log(f"[bold yellow]Генерация графиков включена. Директория: {GRAPHICS_OUTPUT_DIR}[/]")
        manager = GraphicsManager(GRAPHICS_OUTPUT_DIR)

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
        # --- НОВОЕ: Передаем менеджер в функцию ---
        run_fuzzy_logic(raw_data, source_name=f"API_({latitude:.2f}, {longitude:.2f})", manager=manager)
    else:
        console.log("[bold red]Нет данных для запуска системы логики.[/]")


def run_mock_mode():
    """Запускает тестовый режим с использованием данных из `mock_data.json`."""
    # --- НОВОЕ: Инициализация менеджера графиков ---
    manager = None
    if CREATE_GRAPHICS and GraphicsManager:
        console.log(f"[bold yellow]Генерация графиков включена. Директория: {GRAPHICS_OUTPUT_DIR}[/]")
        manager = GraphicsManager(GRAPHICS_OUTPUT_DIR)
        
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
        
        # --- НОВОЕ: Передаем менеджер в функцию ---
        run_fuzzy_logic(mock_scenarios[selected_key], source_name=f"Mock_{selected_key}", manager=manager)

    except FileNotFoundError:
        console.log(f"[bold red]Критическая Ошибка: Файл '{MOCK_FILE}' не найден![/]")
    except Exception:
        console.log("[bold red]Критическая Ошибка в тестовом режиме:[/]"); console.print_exception()


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