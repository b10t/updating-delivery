from django.db import models


class Location(models.Model):
    address = models.CharField(
        unique=True,
        max_length=500,
        verbose_name='Адрес'
    )
    latitude = models.FloatField(
        verbose_name='Широта'
    )
    longitude = models.FloatField(
        verbose_name='Долгота'
    )
    received_at = models.DateTimeField(
        verbose_name='Дата получения данных',
        blank=True
    )

    class Meta:
        verbose_name = 'Местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self) -> str:
        return f'{self.address}'
