# Файл: src/utils/graphics_manager.py
"""
Модуль для управления генерацией и сохранением графиков нечеткой логики.

Включает функционал для отрисовки функций принадлежности входных
и выходных переменных, а также для сборки PNG-изображений в единый PDF-отчет.
"""
import matplotlib
matplotlib.use('Agg')

import os
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import skfuzzy.control as ctrl

from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.utils.logger import console

class GraphicsManager:
    """
    Класс для управления генерацией и сохранением графиков.

    Автоматически создает директорию для отчетов с уникальным именем,
    сохраняет в нее графики и может собрать их в PDF.
    """
    def __init__(self, output_base_dir: str):
        """
        Инициализирует менеджер графиков.

        Args:
            output_base_dir (str): Базовая директория для сохранения отчетов.
        """
        self.output_base_dir = Path(output_base_dir)
        self.report_dir: Path | None = None
        self.image_paths: list[Path] = []
        self._create_unique_report_dir()

    def _create_unique_report_dir(self):
        """Создает уникальную директорию для текущего отчета."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_dir = self.output_base_dir / f"report_{timestamp}"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        console.log(f"[bold green]Создана директория для отчета:[/ bold green] {self.report_dir}")

    def _save_plot(self, fig: plt.Figure, filename: str):
        """Сохраняет Matplotlib фигуру в файл и добавляет путь к списку."""
        if not self.report_dir:
            console.log("[bold red]Ошибка: Директория для отчета не инициализирована.[/]")
            return

        file_path = self.report_dir / filename
        try:
            fig.savefig(file_path, bbox_inches='tight') # bbox_inches='tight' убирает лишние поля
            self.image_paths.append(file_path)
            console.log(f"[grey50]График сохранен:[/grey50] {filename}")
        except Exception as e:
            console.log(f"[bold red]Ошибка при сохранении графика {filename}:[/] {e}")
        finally:
            plt.close(fig) # Всегда закрываем фигуру для освобождения памяти

    def _setup_cyrillic_fonts(self) -> str | None:
        """
        Ищет на компьютере подходящий шрифт с поддержкой кириллицы
        и регистрирует его в reportlab.
        """
        # Список возможных путей к шрифтам для разных ОС
        font_paths = [
            'C:/Windows/Fonts/DejaVuSans.ttf', # Windows (если установлен)
            'C:/Windows/Fonts/Arial.ttf',     # Windows (стандартный)
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', # Linux
            '/System/Library/Fonts/Supplemental/Arial.ttf' # macOS
        ]
        
        font_name = 'DejaVuSans' # Имя, под которым мы регистрируем шрифт

        for path in font_paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, path))
                    console.log(f"[grey50]Шрифт для PDF найден и зарегистрирован:[/grey50] {path}")
                    return font_name
                except Exception as e:
                    console.log(f"[bold yellow]Не удалось загрузить шрифт {path}:[/] {e}")
        
        console.log("[bold red]Ошибка: Не найден подходящий шрифт с кириллицей для PDF. Текст будет некорректным.[/]")
        return None
    
    def save_input_fuzzy_plot(
        self,
        antecedent: ctrl.Antecedent,
        crisp_value: float,
        title: str,
        filename: str
    ):
        """
        Рисует и сохраняет график для одной ВХОДНОЙ переменной.

        Версия 1.3:
        - Добавлена полупрозрачная (alpha=0.5) заливка.
        - Легенда вынесена за пределы графика, чтобы не мешать.

        Args:
            antecedent (ctrl.Antecedent): Объект переменной (np. pm2_5).
            crisp_value (float): "Четкое" входное значение (np. 150.0).
            title (str): Заголовок графика (np. "Вход: PM2.5").
            filename (str): Имя файла для сохранения (np. "pm2_5_input.png").
        """
        try:
            # Увеличиваем ширину, чтобы было место для легенды
            fig, ax = plt.subplots(figsize=(12, 6))
            universe = antecedent.universe

            # Отрисовка всех функций принадлежности (термов)
            for term_name, mf_term in antecedent.terms.items():
                y_values = mf_term.mf
                
                # 1. Рисуем контур
                plot_line = ax.plot(universe, y_values, label=term_name, linewidth=2.0)
                
                # 2. Получаем цвет этого контура
                line_color = plot_line[0].get_color()
                
                # 3. Делаем заливку этим цветом с прозрачностью 0.5
                ax.fill_between(universe, y_values, 0, color=line_color, alpha=0.5)

            # Отрисовка "четкого" входного значения
            label_text = f'Текущее значение: {crisp_value:.2f}'
            ax.vlines(
                crisp_value, 0, 1,
                color='r',
                linestyle='--',
                linewidth=2,
                label=label_text
            )

            # Настройка графика
            ax.set_title(title, fontsize=16, weight='bold')
            ax.set_xlabel('Диапазон значений', fontsize=12)
            ax.set_ylabel('Степень принадлежности', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.6)

            # Выносим легенду за пределы (1.02 = 2% правее от края)
            ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), fontsize=10)

            # Уменьшаем правую границу, чтобы освободить место для легенды
            fig.subplots_adjust(right=0.75)
            
            self._save_plot(fig, filename)

        except Exception as e:
            console.log(f"[bold red]Ошибка при сохранении графика '{filename}':[/] {e}")

    def save_output_fuzzy_plot(
            self,
            simulation: ctrl.ControlSystemSimulation,
            consequent_template: ctrl.Consequent,
            title: str,
            filename: str
        ):
            """
            Рисует и сохраняет график для ВЫХОДНОЙ переменной.

            ВЕРСИЯ 2.0: Добавлена стилизация под входные графики.
            - Легенда выносится за пределы.
            - Черная линия заменяется на красную пунктирную.
            - Добавляется красивая заливка.

            Args:
                simulation (ctrl.ControlSystemSimulation): "Живой" объект симуляции.
                consequent_template (ctrl.Consequent): "Шаблон" выходной переменной.
                title (str): Заголовок графика.
                filename (str): Имя файла для сохранения.
            """
            try:
                # Используем встроенную визуализацию для получения базового графика
                consequent_template.view(sim=simulation)

                # --- ПЕРЕХВАТЫВАЕМ ФИГУРУ И ОСИ ---
                fig = plt.gcf()
                ax = plt.gca()
                fig.set_size_inches(12, 6) # Устанавливаем размер

                # --- НАСТРАИВАЕМ СТИЛЬ ---
                ax.set_title(title, fontsize=16, weight='bold')
                ax.set_xlabel('Диапазон значений', fontsize=12)
                ax.set_ylabel('Степень принадлежности', fontsize=12)
                ax.grid(True, linestyle='--', alpha=0.6)

                # --- УДАЛЯЕМ ОРИГИНАЛЬНУЮ ЧЕРНУЮ ЛИНИЮ И ЛЕГЕНДУ ---
                # Черная линия - это последний элемент, добавленный на график
                ax.lines[-1].remove()
                if ax.legend_:
                    ax.legend_.remove()

                # --- ДОБАВЛЯЕМ СВОЮ КРАСИВУЮ ЛИНИЮ И ЛЕГЕНДУ ---
                defuzz_value = simulation.output[consequent_template.label]
                label_text = f'Итоговое значение: {defuzz_value:.2f}'
                ax.vlines(
                    defuzz_value, 0, 1,
                    color='r',
                    linestyle='--',
                    linewidth=2,
                    label=label_text
                )
                # Выносим легенду за пределы
                ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), fontsize=10)
                fig.subplots_adjust(right=0.75)
                
                # Сохраняем и закрываем
                self._save_plot(fig, filename)

            except Exception as e:
                console.log(f"[bold red]Ошибка при сохранении графика '{filename}':[/] {e}")


    def _get_description_from_filename(self, filename: str) -> tuple[str, str]:
            """Генерирует заголовок и описание на основе имени файла."""
            parts = filename.replace('.png', '').split('_')
            
            # Пример: 01_input_particle_pm2_5
            if "input" in parts and len(parts) >= 4:
                subsystem = parts[2].capitalize()
                variable = parts[3].upper()
                title = f"Этап Фаззификации: Входная переменная '{variable}'"
                description = (
                    f"На данном графике показан процесс фаззификации для переменной <b>{variable}</b> "
                    f"в рамках подсистемы <b>'{subsystem}'</b>. Вертикальная красная линия "
                    f"указывает на четкое входное значение. Пересечение этой линии с "
                    f"функциями принадлежности ('low', 'medium' и т.д.) определяет, "
                    f"с какой степенью (от 0 до 1) входное значение принадлежит каждому "
                    f"из лингвистических термов."
                )
                return title, description

            # Пример: 02_output_particle_risk
            if "output" in parts and len(parts) >= 3:
                variable = " ".join(parts[2:]).title().replace('In', '')
                title = f"Этап Дефаззификации: Выходная переменная '{variable}'"
                description = (
                    f"Этот график иллюстрирует финальные этапы нечеткого вывода для переменной <b>{variable}</b>. "
                    f"Пунктирными линиями обозначены исходные функции принадлежности выходных термов. "
                    f"<b>Фиолетовая область</b> — это итоговая агрегированная фигура, полученная после "
                    f"активации и композиции всех сработавших правил. <b>Красная пунктирная линия</b> "
                    f"указывает на дефаззифицированное значение — 'центр тяжести' этой фигуры, "
                    f"которое и является итоговым четким результатом."
                )
                return title, description
            
            return "График", "Описание отсутствует."

    def generate_pdf_report(self, report_title: str = "Отчет Fuzzy Atmo-Engine"):
        """
        Собирает все сохраненные графики в один полноценный PDF-отчет.
        ИСПРАВЛЕННАЯ ВЕРСИЯ: с поддержкой кириллицы.
        """
        if not self.image_paths:
            console.log("[bold yellow]Предупреждение: Нет графиков для создания PDF-отчета.[/]")
            return

        # --- ИЗМЕНЕНИЕ: Настраиваем шрифты ПЕРЕД созданием документа ---
        font_name = self._setup_cyrillic_fonts()
        
        pdf_path = self.report_dir / f"{report_title.replace(' ', '_')}.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
        styles = getSampleStyleSheet()

        # --- ИЗМЕНЕНИЕ: Применяем наш шрифт ко всем стилям, если он найден ---
        if font_name:
            styles['h1'].fontName = font_name
            styles['h2'].fontName = font_name
            styles['h3'].fontName = font_name
            styles['Normal'].fontName = font_name
            styles['BodyText'].fontName = font_name

        story = []

        # --- 1. Титульная страница ---
        story.append(Paragraph("Fuzzy Atmo-Engine", styles['h1']))
        story.append(Paragraph("Детальный отчет о работе системы нечеткого вывода", styles['h2']))
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph(f"<b>ID Отчета:</b> {self.report_dir.name}", styles['Normal']))
        story.append(Paragraph(f"<b>Дата генерации:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(PageBreak())

        # --- 2. Добавляем каждый график с описанием ---
        for img_path in self.image_paths:
            filename = img_path.name
            title, description = self._get_description_from_filename(filename)

            # Добавляем заголовок для графика
            story.append(Paragraph(title, styles['h3']))
            story.append(Spacer(1, 0.2 * inch))
            
            # Добавляем текстовое описание
            story.append(Paragraph(description, styles['BodyText']))
            story.append(Spacer(1, 0.2 * inch))

            # Добавляем сам график
            img = Image(img_path, width=6*inch, height=3*inch)
            story.append(img)
            story.append(Spacer(1, 0.5 * inch))

            # Разрыв страницы после каждого выходного графика для читаемости
            if "output" in filename:
                story.append(PageBreak())
        
        try:
            doc.build(story)
            console.log(f"[bold green]Полноценный PDF-отчет успешно создан:[/bold green] {pdf_path}")
        except Exception as e:
            console.log(f"[bold red]Ошибка при создании PDF-отчета:[/ bold red] {e}")


# Пример использования (можно закомментировать после отладки)
if __name__ == "__main__":
    from config import GRAPHICS_OUTPUT_DIR
    # Создаем фиктивные переменные для демонстрации
    x = ctrl.Antecedent(np.arange(0, 11, 1), 'x')
    x['low'] = fuzz.trimf(x.universe, [0, 0, 5])
    x['high'] = fuzz.trimf(x.universe, [5, 10, 10])

    y = ctrl.Consequent(np.arange(0, 21, 1), 'y')
    y['small'] = fuzz.trimf(y.universe, [0, 0, 10])
    y['large'] = fuzz.trimf(y.universe, [10, 20, 20])

    rule1 = ctrl.Rule(x['low'], y['small'])
    rule2 = ctrl.Rule(x['high'], y['large'])
    system = ctrl.ControlSystem([rule1, rule2])
    sim = ctrl.ControlSystemSimulation(system)

    sim.input['x'] = 3
    sim.compute()
    
    manager = GraphicsManager(GRAPHICS_OUTPUT_DIR)
    
    # Сохраняем входной график
    manager.save_input_fuzzy_plot(x, 3, "Тестовый вход X", "test_input_x.png")
    
    # Сохраняем выходной график
    manager.save_output_fuzzy_plot(sim, y, sim.output['y'], "Тестовый выход Y", "test_output_y.png")
    
    manager.generate_pdf_report("Тестовый отчет")

    # Проверяем, что отчет создался
    if manager.report_dir:
        console.log(f"Тестовый отчет должен быть в: {manager.report_dir}")