from django.contrib import admin
from .models import Trip, LogSheet, HoursOfService, LogActivity

admin.site.register(Trip)
admin.site.register(LogSheet)
admin.site.register(HoursOfService)
admin.site.register(LogActivity)
