import os
import json
import nest_asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from supabase import create_client, Client
from typing import List, Optional

# ✅ Load environment variables
load_dotenv()
nest_asyncio.apply()

# ✅ Initialize Supabase Client
SUPABASE_URL = os.getenv("supa_")
SUPABASE_KEY = os.getenv("SUPA_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in environment variables!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ Initialize AI Agent
GEMINI_API_KEY = os.getenv("API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in environment variables!")

# ✅ Define Tour Data Model
class Tour(BaseModel):
    name: str
    location: str
    price: float
    duration: str
    description: str

# ✅ Define AI Response Model
class ResponseModel(BaseModel):
    answer: str
    tours: Optional[List[Tour]] = None

# ✅ Fetch or Update User Conversation
def save_conversation(user_id: str, user_query: str, ai_response: str):
    """Fetch or update the conversation history in one record per user."""
    
    try:
        existing_conversation = supabase.table("conversations") \
            .select("messages") \
            .eq("user_id", user_id) \
            .single() \
            .execute()

        messages = existing_conversation.data["messages"] if existing_conversation.data else []
    
    except Exception:
        # If no existing conversation, initialize an empty message list
        messages = []

    # Append new message
    messages.append({"user": user_query, "ai": ai_response})

    # Update or Insert the conversation
    if existing_conversation.data:
        supabase.table("conversations") \
            .update({"messages": messages}) \
            .eq("user_id", user_id) \
            .execute()
    else:
        supabase.table("conversations") \
            .insert([{"user_id": user_id, "messages": messages}]) \
            .execute()

# ✅ Initialize AI Model
model = GeminiModel("gemini-2.0-flash", provider=GoogleGLAProvider(api_key=GEMINI_API_KEY))

# ✅ AI Agent with travel search capabilities
travel_agent = Agent(
    model=model,
    result_type=ResponseModel,
    system_prompt=(
        "You are an AI assistant for a travel agency providing information about available tours and general travel inquiries. "
        "Use the available tools to retrieve real data instead of generating responses. "
        "If a user asks about tour availability, fetch the data from the database."
    ),
)

# ✅ Function to handle conversation with AI
def chat_with_agent(user_id: str, query: str):
    """Handles user chat with AI and stores the conversation."""
    
    result = travel_agent.run_sync(query)

    # Save the conversation to Supabase
    save_conversation(user_id, query, result.data.answer)

    return result.data

# ✅ Test Queries
if __name__ == "__main__":
    test_user_id = "123e4567-e89b-12d3-a456-426614174000"  # Replace with a real user UUID

    test_queries = [
        "I want a trip for summer",
        "Can you suggest something cheaper?",
    ]

    for query in test_queries:
        response = chat_with_agent(test_user_id, query)
        print("\nUser Query:", query)
        print("AI Response:", response)

    print("✅ Conversation saved successfully!")
