import asyncio
from dotenv import load_dotenv
import os
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from supabase import create_client, Client

# ✅ Load environment variables
load_dotenv()

# ✅ Initialize Supabase client
SUPABASE_URL = os.getenv("supa_url")
SUPABASE_KEY = os.getenv("supa_key")

def initialize_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("❌ Supabase credentials are missing!")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

dbconnection: Client = initialize_supabase()
