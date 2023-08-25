from .base import Knowledge
import json, requests
from datetime import datetime, timedelta

class Weather(Knowledge):
    def __init__(self):
        super().__init__()
        self.api_key = self._get_env("WEATHER_KEY")
        self.base_url = "http://api.openweathermap.org/data/2.5/weather?"
        self.forecast_url = "https://api.openweathermap.org/data/2.5/forecast?"

    def query(self, message, action="current", city_name="Champaign"):
        if action == "current":
            return self.current(city_name)
        
        elif action == "forecast":
            return self.forecast(city_name)
        
        return False

    def current(self, city_name):
        complete_url = f"{self.base_url}q={city_name}&appid={self.api_key}&units=imperial"
        print(complete_url)

        response = requests.get(complete_url)

        # Extracting data in JSON format
        data = response.json()
        # Check the HTTP status code
        if response.status_code == 200:
            # Extracting main dictionary block
            main_data = data['main']
            # Extracting temperature from the main_data
            temperature = main_data['temp']
                        
            # Extracting weather report
            weather_data = data['weather']
            weather_description = weather_data[0]['description']

            return f"In {city_name}, it's currently {temperature:.0f}°F with {weather_description}."

        else:
            # API did not return a 200 response
            return f"Error fetching weather for {city_name}."
    

    def forecast(self, city_name):
        complete_url = f"{self.forecast_url}q={city_name}&appid={self.api_key}&units=imperial"
        response = requests.get(complete_url)
        data = response.json()

        if response.status_code != 200:
            return f"Error fetching forecast for {city_name}."
        
        today = datetime.now().date()
        cutoff_date = today + timedelta(days=3)

        forecast_data = {}
        for item in data['list']:
            date = datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S").date()

            if date > cutoff_date:
                continue

            temp_max = item['main']['temp_max']
            temp_min = item['main']['temp_min']
            description = item['weather'][0]['description']

            if date not in forecast_data:
                forecast_data[date] = {
                    "high": temp_max,
                    "low": temp_min,
                    "descriptions": set([description])
                }
            else:
                forecast_data[date]['high'] = max(forecast_data[date]['high'], temp_max)
                forecast_data[date]['low'] = min(forecast_data[date]['low'], temp_min)
                forecast_data[date]['descriptions'].add(description)

        forecast_string = f"Sum the following up in 2 sentences maximum. Today's date is {today}, so you can use relative dates like today and tommorrow. You do not need to be exact with the numbers. You can say high 70's instead of 79.05 for example."
        for date, details in forecast_data.items():
            high = details['high']
            low = details['low']
            descriptions = ", ".join(details['descriptions'])
            forecast_string += f"{date}: High: {high}°F, Low: {low}°F, Descriptions: {descriptions}\n"

        print(forecast_string)

        return forecast_string