# Файл: src/utils/logger.py
from rich.console import Console

"""
Наш "синглтон" логгера.
Мы импортируем этот 'console' объект везде,
"""
console = Console(highlight=True, color_system="auto")
