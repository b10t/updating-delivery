from django.contrib import admin

from .models import Location

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    readonly_fields = ('received_at',)
    list_display = [
        'address',
        'latitude',
        'longitude',
        'received_at',
    ]
