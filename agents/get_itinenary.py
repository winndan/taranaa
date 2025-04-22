import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from models.models import ProcessedItineraryData

# Add project root for imports if needed


load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("Missing API_KEY in environment variables!")



# Initialize Gemini model
model = GeminiModel("gemini-2.0-flash", provider=GoogleGLAProvider(api_key=API_KEY))

# Create the itinerary agent with the model and deps_type
itinerary_agent = Agent(
    model=model,
    deps_type=ProcessedItineraryData,
    result_retries=3,
    system_prompt=(
        "You are a Philippine travel expert. Use 🇵🇭 emoji. "
        "Always include: 1) Current travel/weather conditions 2) Local landmark reference "
        "3) Travel tip 4) Safety alert if needed. Use the search tool for up-to-date info."
    ),
)

async def main():
    try:
        destination = input("Enter Philippine destination: ").strip()
        days = int(input("How many days for your trip? ").strip())
        interests = [i.strip() for i in input("What are your interests? (comma-separated): ").split(",")]
        now = datetime.now()
        current_date_str = now.strftime("%A, %B %d, %Y, %I:%M %p")

        itinerary_data = ProcessedItineraryData(
            destination=destination,
            days=days,
            interests=interests,
            current_date=current_date_str,
            weather=None  # Add weather info here if available
        )

        prompt = (
            f"Generate a real-time {days}-day travel itinerary for {destination} in the Philippines, "
            f"focused on these interests: {', '.join(interests)}. "
            f"Today is {current_date_str}. "
            "Include: 1) Current travel/weather conditions 2) Local landmark reference "
            "3) Travel tip 4) Safety alert if needed. "
            "Format with a clear day-by-day plan and practical advice."
        )

        response = await itinerary_agent.run(prompt, deps=itinerary_data)

        print("\n=== PHILIPPINE ITINERARY REPORT 🇵🇭 ===")
        print(response.output)
        print(f"\nUsage: {response.usage()}")

    except Exception as e:
        print(f"⚠️ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
