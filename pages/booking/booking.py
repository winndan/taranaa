from fasthtml.common import *
from monsterui.all import *


def booking():
    """ Booking Page """
    return Container(
        NavBar(*scrollspy_links),
        DivCentered(H1("Booking Page"), P("Here you can manage your bookings."))
    )