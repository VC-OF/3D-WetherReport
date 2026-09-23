import requests
from datetime import datetime, timedelta

# Calculate dates
today = datetime.now()
week_ago = today - timedelta(days=7)

# Format dates for API (YYYY-MM-DD)
start_date = week_ago.strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")

# Get Paris weather for past week
url = (
    f"https://api.open-meteo.com/v1/forecast?latitude=48.85&longitude=2.35"
    f"&start_date={start_date}&end_date={end_date}"
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
    "windspeed_10m_max&timezone=Europe%2FParis"
)
response = requests.get(url, timeout=30)
response.raise_for_status()
data = response.json()

daili_data = data["daily"]
weather_rows = [
    {
        "date": datetime.strptime(date, "%Y-%m-%d").date(),
        "temperature_2m_max": max_temperature,
        "temperature_2m_min": min_temperature,
        "precipitation_sum": precipitation,
        "windspeed_10m_max": windspeed,
    }
    for date, max_temperature, min_temperature, precipitation, windspeed in zip(
        daili_data["time"],
        daili_data["temperature_2m_max"],
        daili_data["temperature_2m_min"],
        daili_data["precipitation_sum"],
        daili_data["windspeed_10m_max"],
    )
]

for row in weather_rows:
    print(row)