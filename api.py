import json
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests


COUNTRIES = {
    "india": {"name": "India", "city": "New Delhi", "latitude": 28.6139, "longitude": 77.2090},
    "united-kingdom": {"name": "United Kingdom", "city": "London", "latitude": 51.5074, "longitude": -0.1278},
    "japan": {"name": "Japan", "city": "Tokyo", "latitude": 35.6762, "longitude": 139.6503},
    "united-states": {"name": "United States", "city": "New York", "latitude": 40.7128, "longitude": -74.0060},
    "australia": {"name": "Australia", "city": "Sydney", "latitude": -33.8688, "longitude": 151.2093},
    "brazil": {"name": "Brazil", "city": "Brasilia", "latitude": -15.7939, "longitude": -47.8828},
    "canada": {"name": "Canada", "city": "Toronto", "latitude": 43.6532, "longitude": -79.3832},
    "france": {"name": "France", "city": "Paris", "latitude": 48.8566, "longitude": 2.3522},
    "germany": {"name": "Germany", "city": "Berlin", "latitude": 52.5200, "longitude": 13.4050},
    "south-africa": {"name": "South Africa", "city": "Cape Town", "latitude": -33.9249, "longitude": 18.4241},
}


def get_weather_data(country_id):
    location = COUNTRIES[country_id]
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
        "hourly": "temperature_2m,precipitation_probability,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,wind_speed_10m_max",
        "forecast_days": 7,
        "timezone": "auto",
    }
    response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=20)
    response.raise_for_status()
    return {"location": location, **response.json()}


class WeatherHandler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/countries":
            self.send_json(COUNTRIES)
            return
        if parsed.path == "/api/weather":
            country_id = parse_qs(parsed.query).get("country", ["india"])[0]
            if country_id not in COUNTRIES:
                self.send_json({"error": "That country is not available."}, 404)
                return
            try:
                self.send_json(get_weather_data(country_id))
            except requests.RequestException as error:
                self.send_json({"error": f"Weather provider unavailable: {error}"}, 502)
            return
        if parsed.path == "/api/weather/all":
            try:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    results = executor.map(get_weather_data, COUNTRIES)
                    self.send_json({country_id: item for country_id, item in zip(COUNTRIES, results)})
            except requests.RequestException as error:
                self.send_json({"error": f"Weather provider unavailable: {error}"}, 502)
            return
        if parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if parsed.path == "/" or parsed.path == "/index.html":
            page = (Path(__file__).parent / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
            return
        self.send_error(404)

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), WeatherHandler)
    print("Weather dashboard running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping weather dashboard.")
        server.server_close()