import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("WEATHER_API_KEY")

def get_weather(city_name):
    """
    Fetches the current weather for a given city using WeatherAPI.com.

    :param city_name (str): Name of the city.

    Returns:
        str: Formatted string with weather information or an error message.
    """
    base_url = "http://api.weatherapi.com/v1/current.json"
    params = {
        'q': city_name,
        'key': api_key,
        'aqi': 'no'
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        location = data['location']['name']
        region = data['location']['region']
        country = data['location']['country']
        condition = data['current']['condition']['text']
        temp_c = data['current']['temp_c']
        feelslike_c = data['current']['feelslike_c']
        humidity = data['current']['humidity']
        wind_kph = data['current']['wind_kph']

        return (
            f"🌤️ Weather in {location}, {region}, {country}:\n"
            f"- Condition: {condition}\n"
            f"- Temperature: {temp_c}°C (Feels like {feelslike_c}°C)\n"
            f"- Humidity: {humidity}%\n"
            f"- Wind Speed: {wind_kph} km/h"
        )
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except requests.exceptions.RequestException as req_err:
        return f"Request error occurred: {req_err}"
    except KeyError:
        return "Error: Unable to retrieve weather data. Please check the city name and try again."


# def get_weather(city: str):
#     url = f"https://wttr.in/{city}?format=j1"
#     try:
#         response = requests.get(url)
#         data = response.json()

#         current = data["current_condition"][0]
#         weather_desc = current["weatherDesc"][0]["value"]
#         temp_c = current["temp_C"]
#         feels_like_c = current["FeelsLikeC"]
#         humidity = current["humidity"]
#         wind_kmph = current["windspeedKmph"]

#         return (
#             f"🌤️ Weather in {city.title()}:\n"
#             f"- Condition: {weather_desc}\n"
#             f"- Temperature: {temp_c}°C (Feels like {feels_like_c}°C)\n"
#             f"- Humidity: {humidity}%\n"
#             f"- Wind Speed: {wind_kmph} km/h"
#         )
#     except Exception as e:
#         return f"Exception occurred: {str(e)}"
