import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import requests
from datetime import datetime
from dotenv import load_dotenv
from models.models import ProcessedWeatherData
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

load_dotenv()

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("Missing API_KEY in environment variables!")

def get_lat_lon_ph(location: str):
    url = (
        f"https://geocoding-api.open-meteo.com/v1/search"
        f"?name={location}&country=PH&count=1&language=en"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    results = resp.json().get("results")
    if not results:
        raise ValueError(
            f"Location '{location}' not found in the Philippines. "
            "Check spelling or see: https://en.wikipedia.org/wiki/List_of_cities_and_municipalities_in_the_Philippines"
        )
    return results[0]["latitude"], results[0]["longitude"], results[0]["name"]

def get_ph_weather(location: str) -> ProcessedWeatherData:
    try:
        lat, lon, resolved_name = get_lat_lon_ph(location)
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            "&current=temperature_2m,windspeed_10m,weather_code,is_day,precipitation,relative_humidity_2m"
            "&timezone=Asia/Manila"
        )
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        current = data["current"]
        return ProcessedWeatherData(
            location_name=resolved_name,
            coordinates=f"{lat},{lon}",
            temperature=current["temperature_2m"],
            windspeed=current["windspeed_10m"],
            weather_code=current["weather_code"],
            is_day=bool(current["is_day"]),
            time=current["time"],
            precipitation=current.get("precipitation"),
            humidity=current.get("relative_humidity_2m")
        )
    except Exception as e:
        raise RuntimeError(str(e))

model = GeminiModel(
    "gemini-2.0-flash",
    provider=GoogleGLAProvider(api_key=API_KEY)
)

weather_agent = Agent(
    model=model,
    deps_type=ProcessedWeatherData,
    result_retries=3,
    system_prompt=(
        "Philippine weather expert. Use 🇵🇭 emoji. Include:\n"
        "1. Current condition\n2. Local landmark reference\n"
        "3. Travel tip\n4. Safety alert if needed"
    ),
)

async def main():
    try:
        location = input("Enter Philippine location: ").strip()
        weather = get_ph_weather(location)

        # Get the current date and time (system time, local)
        now = datetime.now()
        current_date_str = now.strftime("%A, %B %d, %Y, %I:%M %p %Z")
        # If you want PH time, use pytz or zoneinfo for 'Asia/Manila'

        prompt = (
            f"Generate a real-time weather report for {weather.location_name} on {current_date_str}:\n"
            f"- Temperature: {weather.temperature}°C\n"
            f"- Wind: {weather.windspeed} m/s\n"
            f"- Condition: {weather.condition_description}\n"
            f"- Daytime: {'Yes' if weather.is_day else 'No'}\n"
            f"- Observed at: {weather.time} (PHST)\n\n"
            "Include emoji and local advice."
        )

        response = await weather_agent.run(prompt, deps=weather)

        print("\n=== PHILIPPINE WEATHER REPORT 🇵🇭 ===")
        print(response.output)
        print(f"\nUsage: {response.usage()}")

    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
