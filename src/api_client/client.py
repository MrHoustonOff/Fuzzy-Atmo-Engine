# Файл: src/api_client/client.py
import requests
from config import API_BASE_URL, CURRENT_PARAMS, HOURLY_PARAMS


class AirQualityClient:
    """
    Модульный клиент для "парсинга" данных о качестве воздуха
    с Open-Meteo.
    """
    def __init__(self):
        self.base_url = API_BASE_URL

    def get_air_quality(self, latitude: float, longitude: float) -> dict:
        """
        Главный метод. Делает GET-запрос к API.

        Возвращает "сырой" JSON-ответ в виде словаря (dict).
        В случае ошибки - выбрасывает исключение.
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

            # Автоматически "упасть", если API вернул ошибку (напр., 404, 500)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP Error: {http_err}")
            raise  # Пробрасываем ошибку наверх
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection Error: {conn_err}")
            raise
        except requests.exceptions.RequestException as err:
            print(f"Opps: Something Else: {err}")
            raise
