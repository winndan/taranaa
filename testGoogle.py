import os
from fasthtml.common import *
from fasthtml.oauth import GoogleAppClient, redir_url
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize database
db = database('data/counts.db')
counts = db.t.counts
if counts not in db.t:
    counts.create(dict(name=str, count=int), pk='name')
Count = counts.dataclass()

# Google OAuth client setup
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError("Missing Google OAuth credentials in .env file!")

client = GoogleAppClient(
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ]
)

# Ensure the redirect URI is set correctly
auth_callback_path = "/auth_redirect"
REDIRECT_URI = "http://localhost:5001/auth_redirect"  # Change if deployed

def before(req, session):
    auth = req.scope['auth'] = session.get('user_id', None)
    if not auth:
        return RedirectResponse('/login', status_code=303)
    counts.xtra(name=auth)

bware = Beforeware(before, skip=['/login', auth_callback_path])
app = FastHTML(before=bware)

# Login Route
@app.get('/login')
def login(request, session):
    if "user_id" in session:
        return RedirectResponse("/", status_code=303)
    
    login_link = client.login_link(REDIRECT_URI)
    return P(A(Img(src="https://developers.google.com/identity/images/btn_google_signin_light_normal_web.png", width=200), href=login_link))

# OAuth Callback - Retrieves User Info
@app.get(auth_callback_path)
def auth_redirect(code: str, request, session):
    try:
        user_info = client.retr_info(code, REDIRECT_URI)

        # Debugging: Print the user info response
        print("Google User Info Response:", user_info)

        session['user_id'] = user_info.get("sub", "Unknown ID")
        session['name'] = user_info.get("name", "Unknown User")
        session['given_name'] = user_info.get("given_name", "Unknown")
        session['family_name'] = user_info.get("family_name", "Unknown")
        session['email'] = user_info.get("email", "Unknown Email")

        # Ensure profile picture URL is correctly formatted
        profile_pic = user_info.get("picture", "https://via.placeholder.com/100")
        if profile_pic and "googleusercontent.com" in profile_pic:
            profile_pic = profile_pic.split("=")[0] + "?sz=200"

        session['picture'] = profile_pic

        print("Final Profile Image URL:", session['picture'])  # Debugging

        session['gender'] = user_info.get("gender", "Not Provided")
        session['location'] = user_info.get("locale", "Not Provided")

        if session['user_id'] not in counts:
            counts.insert(name=session['user_id'], count=0)

        return RedirectResponse('/', status_code=303)

    except Exception as e:
        print("OAuth Error:", str(e))
        return P("Authentication failed. Please try again.", A("Go back to login", href="/login"))

# Home Page - Displays User Profile
@app.get('/')
def home(auth, session):
    profile_image = session.get('picture', "https://via.placeholder.com/100")
    print("Rendering Profile Image URL:", profile_image)  # Debugging
    return Div(
        P("Welcome to Count Demo"),
        Img(src=profile_image, width=100, height=100, alt="Profile Picture", style="border-radius:50%"),
        P(f"Name: {session.get('name', 'Unknown')}"),
        P(f"Given Name: {session.get('given_name', 'Unknown')}"),
        P(f"Family Name: {session.get('family_name', 'Unknown')}"),
        P(f"Email: {session.get('email', 'Unknown')}"),
        P(f"Google ID: {session.get('user_id', 'Unknown')}"),
        P(f"Gender: {session.get('gender', 'Not Provided')}"),
        P(f"Location: {session.get('location', 'Not Provided')}"),
        P(f"Count: ", Span(counts[auth].count, id='count')),
        Button('Increment', hx_get='/increment', hx_target='#count'),
        P(A('Logout', href='/logout'))
    )

# Increment Count
@app.get('/increment')
def increment(auth):
    c = counts[auth]
    c.count += 1
    return counts.upsert(c).count

# Logout - Clears Session
@app.get('/logout')
def logout(session):
    session.clear()
    return RedirectResponse("https://accounts.google.com/Logout")




# Start the application
serve()