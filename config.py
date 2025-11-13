# Файл: config.py

# Базовый URL для Air Quality API
API_BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# набор параметров
# (Мы берем 9 + 2 AQI для сверки)
CURRENT_PARAMS = [
    "pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide",
    "sulphur_dioxide", "ozone", "aerosol_optical_depth",
    "dust", "ammonia", "european_aqi", "us_aqi"
]

HOURLY_PARAMS = CURRENT_PARAMS  # тот же набор для прогноза часового
