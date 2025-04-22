from fasthtml import App, Request, Response
from fasthtml.oauth import GoogleAppClient
from fasthtml.common import RedirectResponse
import requests
import jwt
import datetime
import supabase
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")  # This secret key is used to sign JWT tokens for authentication.
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Initialize OAuth without passing credentials initially
oauth = GoogleAppClient(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_uri=GOOGLE_REDIRECT_URI
)

# Initialize Supabase client
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastHTML()

@app.get("/login")
def login(req: requests):
    """Redirect user to Google OAuth login page."""
    auth_url = oauth.login_link(
        req, 
        client_id=GOOGLE_CLIENT_ID,
        redirect_uri=GOOGLE_REDIRECT_URI, 
        scopes=["openid", "email", "profile", "https://www.googleapis.com/auth/user.birthday.read"], 
        prompt="consent", 
        access_type="offline"
    )
    return Response.redirect(auth_url)

@app.get("/redirect")
def google_callback(req: requests):
    """Handle Google OAuth callback."""
    code = req.query_params.get("code")
    if not code:
        return Response.json({"error": "Missing authorization code"}, status=400)
    
    # Exchange code for tokens
    info = oauth.retr_info(
        code, 
        client_id=GOOGLE_CLIENT_ID, 
        client_secret=GOOGLE_CLIENT_SECRET, 
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    
    email = info.get("email")
    name = info.get("name", "Unknown")
    picture = info.get("picture", "")
    birthdate = info.get("birthdate", "Unknown")  # Fetch age-related info
    
    # Check if user exists in Supabase
    response = supabase_client.table("users").select("*").eq("email", email).execute()
    if not response.data:
        supabase_client.table("users").insert({"email": email, "name": name, "picture": picture, "birthdate": birthdate}).execute()
    
    # Generate JWT token
    jwt_token = jwt.encode({"sub": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, SECRET_KEY, algorithm=ALGORITHM)
    
    return RedirectResponse("/", headers={"Authorization": f"Bearer {jwt_token}"})

@app.get("/")
def home(auth):
    """User home page after login."""
    return Response.html(f"<p>Logged in!</p><a href='/logout'>Log out</a>")

@app.get("/logout")
def logout(req: requests):
    """Logout the user."""
    return RedirectResponse("/")

if __name__ == "__main__":
    serve()
