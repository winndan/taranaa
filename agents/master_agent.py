import sys
import os
import asyncio
import json
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from datetime import datetime

# Setup imports from parent dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.get_weather import weather_agent
from agents.get_rooms import room_agent
from agents.get_itinenary import itinerary_agent
from models.models import ProcessedItineraryData, ProcessedWeatherData

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing API_KEY in environment variables!")

model = GeminiModel("gemini-2.0-flash", provider=GoogleGLAProvider(api_key=GEMINI_API_KEY))

# Master agent for parsing and routing
router_agent = Agent(
    model=model,
    result_retries=3,
    system_prompt=(
        "You are an intent parser and router. Extract from the user query:\n"
        "- intent: 'weather', 'rooms', 'itinerary', or combinations like 'weather+itinerary'\n"
        "- destination (string, optional)\n"
        "- days (integer, optional)\n"
        "- interests (list of strings, optional)\n"
        "Respond in this JSON format:\n"
        "{ \"intent\": \"weather+itinerary\", \"destination\": \"Ilocos Sur\", \"days\": 5, \"interests\": [\"food\", \"beaches\"] }\n"
        "Make sure your response is strictly valid JSON with double quotes around keys and string values."
    )
)

async def route_query(user_query: str):
    # Get parsed response from the router agent
    parse_response = await router_agent.run(user_query)
    
    # Check if the response is a valid object
    try:
        output = parse_response.output.strip()  # Use .output and strip whitespace
        
        # Try to parse as JSON
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            # If the output isn't valid JSON, try to extract just the JSON part
            # Look for content between curly braces
            import re
            json_match = re.search(r'({.*})', output, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                except:
                    return f"⚠️ Could not parse JSON from response: {output}"
            else:
                return f"⚠️ No valid JSON found in response: {output}"

        intent = data.get("intent", "").lower()
        destination = data.get("destination")
        days = data.get("days", 1)  # Default to 1 day if not specified
        interests = data.get("interests", [])

    except Exception as e:
        return f"⚠️ Error parsing response: {str(e)}\nRaw output: {parse_response.output}"

    now = datetime.now()
    current_date_str = now.strftime("%A, %B %d, %Y, %I:%M %p")

    # Handle itinerary + weather combination
    if "itinerary" in intent:
        weather = None
        if "weather" in intent and destination:
            # Fetch weather data for the destination
            weather_data = await weather_agent.run(f"Give me the weather for {destination}", deps={"location_name": destination})
            if hasattr(weather_data, "output"):  # Changed from data to output
                weather = weather_data.output  # Changed from data to output

        itinerary_data = ProcessedItineraryData(
            destination=destination,
            days=days,
            interests=interests,
            current_date=current_date_str,
            weather=weather,
        )

        itinerary_prompt = (
            f"Create a {days}-day itinerary for {destination} with interests {', '.join(interests)}. "
            f"Include weather, food, beaches, travel tips, safety alerts. Today is {current_date_str}."
        )
        return await itinerary_agent.run(itinerary_prompt, deps=itinerary_data)

    elif "weather" in intent:
        if destination:
            # Fetch weather report if weather is mentioned
            return await weather_agent.run(f"Give me a weather and safety report for {destination}", deps={"location_name": destination})

    elif "rooms" in intent:
        # Fetch rooms availability if rooms are mentioned
        return await room_agent.run(f"Get available rooms in {destination or 'any city'}")

    return "❓ Sorry, couldn't determine what you're asking. Try asking about itinerary, weather, or rooms."

# Run CLI loop
async def main():
    try:
        while True:
            user_query = input("\n💬 Ask something (or type 'exit'): ").strip()
            if user_query.lower() == "exit":
                print("👋 Exiting.")
                break

            print("🔄 Processing your request...")
            response = await route_query(user_query)
            if isinstance(response, str):
                print(response)
            else:
                print("\n✅ RESPONSE:")
                print(response.output)  # Always use output instead of data
                print("\n📊 USAGE:")
                print(response.usage())

    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())