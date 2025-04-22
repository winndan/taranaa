from fasthtml.common import *
from monsterui.all import *

def profile():
    """ Profile Page """
    return Container(
        NavBar(*scrollspy_links),
        DivCentered(H1("Profile Page"), P("Manage your user profile and settings."))
    )