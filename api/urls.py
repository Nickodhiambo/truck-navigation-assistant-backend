from django.urls import path, include
from .views import (
    CurrentHoursView, RecentTripsView, RoutePlannerView, reverse_geocode
)


urlpatterns = [
    path('hours-of-service/current/', CurrentHoursView.as_view(), name='current-hours'),
    path('trips/recent/', RecentTripsView.as_view(), name='recent-trips'),
    path('routes/plan/', RoutePlannerView.as_view(), name='plan-route'),
    path('geocode/reverse/', reverse_geocode, name='reverse-geocode'),
]