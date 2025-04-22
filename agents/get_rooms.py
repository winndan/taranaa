import sys
import os
# 🔧 Add project root to sys.path for proper imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from models.models import roomInfo
from utils.db_con import dbconnection



# Load environment variables
load_dotenv()

# API key setup
GEMINI_API_KEY = os.getenv("API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in environment variables!")

# Initialize model
model = GeminiModel("gemini-2.0-flash", provider=GoogleGLAProvider(api_key=GEMINI_API_KEY))

# Database connection setup
db = dbconnection

# Create agent
room_agent = Agent(
    model=model,
    deps_type=roomInfo,
    result_retries=3,
    system_prompt="You are an assistant for getting information about rooms.",
)

@room_agent.tool()
def get_rooms(context: RunContext) -> list:
    """Fetch rooms data from Supabase."""
    try:
        response = db.from_("rooms").select("*").execute()
        
        if response.data is None:
            return ["No data found in the rooms table."]
        
        available = [room for room in response.data if room["status"] == "Available"]
        occupied = [room for room in response.data if room["status"] == "Occupied"]
        
        result = {
            "total_rooms": len(response.data),
            "available_rooms": len(available),
            "occupied_rooms": len(occupied),
            "rooms": response.data
        }
        
        return result
    
    except Exception as e:
        return [f"An error occurred: {str(e)}"]

# Main function to run agent
async def main():
    try:
        response = await room_agent.run("Get me all the rooms, count the available and occupied rooms, and give the price details.")
        print(response.data)
        print(response.usage())
    except Exception as e:
        if "API key expired" in str(e):
            print("Error: The API key has expired. Please renew it.")
        else:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
