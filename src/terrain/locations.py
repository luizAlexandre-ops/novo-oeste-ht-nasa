from typing import NamedTuple


class Location(NamedTuple):
    name: str
    latitude: float
    longitude: float


SHACKLETON_CRATER = Location("Shackleton", -89.9, 129.8)
HAWORTH_CRATER = Location("Haworth", -87.5, -5.0)

EARTH_ANALOG_SITES = [
    Location("Meteor Crater (EUA)", 35.027, -111.023),
    Location("Pinacate (México)", 31.95, -113.50),
    Location("Tolbachik (Rússia)", 55.83, 160.38),
]
