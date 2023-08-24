from .base import Knowledge
import json, requests

class Weather(Knowledge):
    def __init__(self):
        super().__init__()
        self.api_key = self._get_env("WEATHER_KEY")
        self.base_url = "http://api.openweathermap.org/data/2.5/weather?"

    def query(self, message, city_name="Champaign"):

        # Constructing the full URL
        complete_url = f"{self.base_url}q={city_name}&appid={self.api_key}&units=imperialh"
        print(complete_url)

        # Getting the response from the API
        response = requests.get(complete_url)

        # Extracting data in JSON format
        data = response.json()
        # Check the HTTP status code
        if response.status_code == 200:
            # Extracting main dictionary block
            main_data = data['main']
            # Extracting temperature from the main_data
            temperature = main_data['temp']
            
            # Converting Kelvin to Celsius for temperature
            temperature_celsius = temperature - 273.15
            
            # Extracting weather report
            weather_data = data['weather']
            weather_description = weather_data[0]['description']

            return f"In {city_name}, it's currently {temperature_celsius:.2f}°C with {weather_description}."

        else:
            # API did not return a 200 response
            return f"Error fetching weather for {city_name}."