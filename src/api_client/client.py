# Файл: src/api_client/client.py
"""
Модуль для взаимодействия с API качества воздуха Open-Meteo.

Содержит класс AirQualityClient, который инкапсулирует логику
формирования запроса, его отправки и базовой обработки ответа.
"""
import requests
from config import API_BASE_URL, CURRENT_PARAMS, HOURLY_PARAMS


class AirQualityClient:
    """
    Клиент для получения данных о качестве воздуха с Open-Meteo.
    """
    def __init__(self):
        """Инициализирует клиент, устанавливая базовый URL API."""
        self.base_url = API_BASE_URL

    def get_air_quality(self, latitude: float, longitude: float) -> dict:
        """
        Выполняет GET-запрос к API для получения данных о качестве воздуха.

        Args:
            latitude (float): Широта для запроса данных.
            longitude (float): Долгота для запроса данных.

        Returns:
            dict: Словарь с "сырыми" данными от API в формате JSON.

        Raises:
            requests.exceptions.RequestException: В случае возникновения
                любой ошибки, связанной с запросом (например, проблемы
                с сетью, HTTP-ошибки 4xx/5xx).
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(CURRENT_PARAMS),
            "hourly": ",".join(HOURLY_PARAMS),
            "timezone": "auto"
        }

        try:
            response = requests.get(self.base_url, params=params)
            # Проверяет, был ли ответ успешным (статус-код 2xx).
            # Если нет, выбрасывает исключение HTTPError.
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # Вместо вывода в консоль здесь, мы "пробрасываем"
            # исключение дальше. Вызывающий код (в main.py)
            # должен будет его поймать и решить, как уведомить пользователя.
            # Это делает клиент более универсальным и переиспользуемым.
            raise e