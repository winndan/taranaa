from fasthtml.common import *
from monsterui.all import *
import random
import json
from agents.master_agent import route_query
from testChat import chatchat, on_connect, on_disconnect
import testChat  # Import the entire testChat module

# Using the "slate" theme with Highlight.js enabled
hdrs = Theme.slate.headers(highlightjs=True)
app, rt = fast_app(hdrs=hdrs, exts='ws')

################################
### Example Data and Content ###
################################
trips = [
    {"name": "Beach Getaway", "price": "$499", "category": "Beach"},
    {"name": "Mountain Hiking", "price": "$599", "category": "Adventure"},
    {"name": "City Tour", "price": "$399", "category": "Urban"},
    {"name": "Safari Expedition", "price": "$999", "category": "Wildlife"},
    {"name": "Cruise Trip", "price": "$1299", "category": "Luxury"},
    {"name": "Skiing Adventure", "price": "$799", "category": "Winter Sports"},
    {"name": "Desert Safari", "price": "$699", "category": "Adventure"},
    {"name": "Island Hopping", "price": "$899", "category": "Beach"},
    {"name": "Cultural Immersion", "price": "$499", "category": "Culture"},
    {"name": "Road Trip", "price": "$299", "category": "Budget"},
    {"name": "Road Trip", "price": "$299", "category": "Awit"},
    {"name": "Road Trip", "price": "$299", "category": "Test"},
    {"name": "Road Trip", "price": "$299", "category": "Zebu"},
    {"name": "Beach Getaway", "price": "$499", "category": "makati"},
    {"name": "Mountain Hiking", "price": "$599", "category": "manila"},
    {"name": "City Tour", "price": "$399", "category": "Cavite"},
    {"name": "Safari Expedition", "price": "$999", "category": "Ilocos"},
    {"name": "Cruise Trip", "price": "$1299", "category": "Taguig"},
    {"name": "Skiing Adventure", "price": "$799", "category": "Winter Sports"},
]

CATEGORIES = sorted(set(t["category"] for t in trips))
ITEMS_PER_PAGE = 10

def TripCard(t, img_id=1):
    return Card(
        PicSumImg(w=500, height=100, id=img_id),
        DivFullySpaced(
            H4(t["name"]),
            P(Strong(t["price"], cls=TextT.sm)),
            P(Em(t["category"], cls=TextT.xs, style="color: gray; font-weight: bold;"))  # Category indicator
        ),
        Button("Details", cls=(ButtonT.primary, "w-full"))
    )


################################
### Reusable NavBar Function ###
################################

def reusable_navbar():
    """Reusable NavBar component"""
    scrollspy_links = (
        A("Explore", href="/"),
        A("Booking", href="/booking"),
        A("Profile", href="/profile"),
        A("Agent", href="/agent"),
        Button("Logout", cls=ButtonT.destructive)
    )
    
    return NavBar(
        *scrollspy_links,
        brand=DivLAligned(H3("Trip Explorer"), 
                          Img(src='assets/logo.png', alt='Coinsumer Logo', cls='logo-img', height=70, width=70)),
        sticky=True, uk_scrollspy_nav=True,
        scrollspy_cls=ScrollspyT.bold
    )


################################
### Category Tabs Function ###
################################

def category_tabs(active_category):
    return TabContainer(
        *[
            Li(
                A(
                    cat, 
                    href=f"/?category={cat}", 
                    cls=('uk-active uk-text-bold uk-text-primary' if cat == active_category else 'uk-text-muted'),
                    style="border-bottom: 2px solid black;" if cat == active_category else ""
                )
            ) 
            for cat in CATEGORIES
        ]
    )


################################
### Pagination Controls ###
################################

def pagination_controls(page, total_pages, category):
    """Generates simple and clean pagination controls."""
    return DivCentered(
        Div(
            A("← Prev", href=f"/?page={page - 1}&category={category}" if page > 1 else "#", cls=ButtonT.primary if page > 1 else "uk-disabled"),
            Span(f" Page {page} of {total_pages} ", cls="uk-text-bold uk-margin-small"),
            A("Next →", href=f"/?page={page + 1}&category={category}" if page < total_pages else "#", cls=ButtonT.primary if page < total_pages else "uk-disabled"),
            cls="uk-flex uk-flex-center uk-gap-small uk-margin-large"
        )
    )


################################
### Explore Page ###
################################

@rt("/search")
def search(query: str = ""):
    """ Handle Search Query """
    filtered_trips = [t for t in trips if query.lower() in t["name"].lower()]
    
    return Div(
        *[TripCard(t, img_id=i) for i, t in enumerate(filtered_trips)],
        cls="uk-grid-match"
    )


@rt
def index(page: int = 1, category: str = "", query: str = ""):
    """ Explore Page with Pagination and Search """
    filtered_trips = [t for t in trips if (category == "" or t["category"] == category) and query.lower() in t["name"].lower()]
    total_pages = (len(filtered_trips) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    paginated_trips = filtered_trips[start_idx:end_idx]

    return Container(
        reusable_navbar(),  # Reusable NavBar
        Container(
            DivCentered(
                H1("Discover Amazing Trips!"),
                A(Input(
                    placeholder="Search...",
                    cls="w-3/4 p-2 rounded-lg h-8 border border-gray-300 text-base", 
                    id="search-input",
                    name="query",  
                    hx_get="/search",  
                    hx_target="#trips-section",  
                    hx_trigger="input changed delay:300ms",  
                    hx_include="[name='query']",  
                    value=query  
                )),
                id="welcome-section"
            ),
            Div(category_tabs(category), cls="w-full flex justify-center items-center mb-6"),
            Section(
                H2(f"Trips in {category}" if category else "All Trips", cls="text-center text-4xl font-extrabold text-gray-900 bg-gradient-to-r from-[#FF5733] to-[#FFC0CB] text-white py-4 px-8 rounded-xl shadow-lg tracking-wide mb-6"),
                Grid(*[TripCard(t, img_id=i) for i, t in enumerate(paginated_trips)], cols_lg=2),
                pagination_controls(page, total_pages, category),
                id="trips-section"
            ),
            cls=(ContainerT.xl, 'uk-container-expand')
        )
    )


################################
### Booking Page ###
################################

def Tags(cats): return DivLAligned(map(Label, cats))

def get_user_bookings():
    """ Fetch user bookings from the bookings.json file. """
    with open('bookings.json', 'r') as f:
        return json.load(f)

@rt("/booking")
def booking():
    """ Booking Page """
    bookings = get_user_bookings()  # Fetch user bookings from JSON data
    
    booking_cards = [
        Card(
            DivLAligned(
                A(Img(src="https://picsum.photos/200/200?random={}".format(booking["id"]), style="width:200px"), href="#"),
                Div(cls='space-y-3 uk-width-expand')(
                    H4(booking["guest_name"]),
                    P(f"Room Number: {booking['room_number']}"),
                    P(f"Check-in: {booking['check_in_date']}"),
                    P(f"Check-out: {booking['check_out_date']}"),
                    P(f"Guests: {booking['number_of_guests']}"),
                    P(Strong(f"${booking['total_price']:.2f}"), cls=TextT.sm),
                    P(f"Status: {booking['status']}", cls=TextT.muted),
                    DivFullySpaced(
                        Tags([booking["payment_method"]] + 
                             ([booking.get("reference_number", "N/A")] if booking["payment_method"] == "eCash" else [])),
                        Button("View Details", cls=(ButtonT.primary, 'h-6'), on_click=f"/booking/{booking['id']}")
                    )
                )
            ),
            cls=CardT.hover
        )
        for booking in bookings
    ]
    
    return Container(
        reusable_navbar(),  # Reusable NavBar
        DivCentered(
            H1("Booking Page", cls="text-center text-4xl font-extrabold text-gray-900 bg-gradient-to-r from-[#FF5733] to-[#FFC0CB] text-white py-4 px-8 rounded-xl shadow-lg tracking-wide mb-6")
        ),
        DivCentered(
            P("Here you can manage your trip bookings.", cls="mb-6")  # Added bottom margin for space
        ),
        Div(
            *booking_cards,  # Display booking cards
            cls="mt-6"  # Margin top for spacing between paragraph and cards
        )
    )


################################
### Profile Page ###
################################

@rt("/profile")
def profile():
    """ Profile Page """
    # Load user data from profile.json
    try:
        with open('profile.json', 'r') as f:
            user_data = json.load(f)
    except Exception as e:
        # Raise an error if profile.json can't be loaded or is missing
        raise FileNotFoundError("The profile.json file could not be loaded. Please check the file.")

    def FormSectionDiv(*c, cls='space-y-2', **kwargs): 
        return Div(*c, cls=cls, **kwargs)

    def FormLayout(title, subtitle, *content, cls='space-y-3 mt-4'):
        return Container(Div(H3(title), Subtitle(subtitle, cls="text-primary"), DividerLine(), Form(*content, cls=cls)))

    def profile_form():
        content = (
            FormSectionDiv(
                LabelInput("Username", placeholder='sveltecult', id='username', value=user_data['fullName']),
                P("This is your public display name.", cls="text-primary")),
            FormSectionDiv(
                FormLabel("Email"),
                Input(value=user_data['email'], readonly=True),  # Display email as read-only
                P("This is your registered email address.", cls="text-primary")),
            FormSectionDiv(
                FormLabel("Profile Picture"),
                Img(src=user_data['profilePicture'], cls="w-24 h-24 rounded-full"),  # Display profile picture
                P("This profile picture is fetched from your Google account.", cls="text-primary"))
        )
        
        return FormLayout('Profile', 'This is how others will see you.', *content)

    # Return the container without sidebar
    return Container(
        reusable_navbar(),  # Reusable NavBar
        DivCentered(  # Center content
            profile_form()
        )
    )

@app.ws('/ws', conn=testChat.on_connect, disconn=testChat.on_disconnect)
async def ws(msg: str, send):
    await testChat.ws(msg, send)

@rt("/agent")
async def agent(request):
    return Container(
        reusable_navbar(),
        await testChat.chatchat(request)  # Render the chatbot
    )


# Run the app
serve()
