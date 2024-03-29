# Generated by Django 3.2 on 2022-08-16 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geolocation', '0002_alter_location_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='latitude',
            field=models.FloatField(blank=True, verbose_name='Широта'),
        ),
        migrations.AlterField(
            model_name='location',
            name='longitude',
            field=models.FloatField(blank=True, verbose_name='Долгота'),
        ),
    ]
