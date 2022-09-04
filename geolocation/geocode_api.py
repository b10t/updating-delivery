import requests

import geolocation.models as geocode_models


def calculate_distance(address_from, address_to):
    """Возвращает расстояние между двумя адресами."""
    if distance := geocode_models.Location.calculate_distance(address_from, address_to):
        return round(distance, 2)


def fetch_coordinates_from_api(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json(
    )['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat
