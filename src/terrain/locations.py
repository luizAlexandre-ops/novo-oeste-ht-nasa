from typing import NamedTuple


class Location(NamedTuple):
    name: str
    latitude: float
    longitude: float


SHACKLETON_CRATER = Location("Shackleton", -89.9, 129.8)
HAWORTH_CRATER = Location("Haworth", -87.5, -5.0)

EARTH_ANALOG_SITES = [
    Location("Atacama", -23.5, -68.2),
    Location("Haughton Crater", 75.37, -89.68),
    Location("Death Valley", 36.24, -116.82),
    Location("Pinacate", 31.95, -113.50),
    Location("Tolbachik", 55.83, 160.38),
    Location("Meteor Crater", 35.027, -111.023),
]
