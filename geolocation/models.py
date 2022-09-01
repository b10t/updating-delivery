from django.conf import settings
from django.db import models
from django.utils import timezone
from geopy.distance import distance, lonlat

from .geocode_api import fetch_coordinates_from_api


class Location(models.Model):
    address = models.CharField(
        db_index=True,
        unique=True,
        max_length=500,
        verbose_name='Адрес'
    )
    latitude = models.FloatField(
        verbose_name='Широта',
        blank=True,
        null=True
    )
    longitude = models.FloatField(
        verbose_name='Долгота',
        blank=True,
        null=True
    )
    received_at = models.DateTimeField(
        verbose_name='Дата получения данных',
        blank=True
    )

    @staticmethod
    def get_coordinates(address):
        """Возвращает координаты по адресу."""
        yandex_api_key = settings.YANDEX_API_KEY

        try:
            coords = Location.objects.get(address=address)
            coords = (coords.longitude, coords.latitude)

        except Location.DoesNotExist:
            if coords := fetch_coordinates_from_api(yandex_api_key, address):
                longitude, latitude = coords

                if coords:
                    Location.objects.create(
                        address=address,
                        longitude=longitude,
                        latitude=latitude,
                        received_at=timezone.now()
                    )

        return coords

    @staticmethod
    def calculate_distance(address_from, address_to):
        """Рассчитывает расстояние между двумя адресами."""
        coords_from = Location.get_coordinates(address_from)
        coords_to = Location.get_coordinates(address_to)

        if coords_from and coords_to:
            return distance(lonlat(*coords_from), lonlat(*coords_to)).km

        return None

    class Meta:
        verbose_name = 'Местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self) -> str:
        return self.address
