from django.contrib import admin
from .models import Trip, LogSheet, HoursOfService

admin.site.register(Trip)
admin.site.register(LogSheet)
admin.site.register(HoursOfService)
