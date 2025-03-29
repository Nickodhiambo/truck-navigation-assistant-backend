from django.urls import path, include
from .views import (
    CurrentHoursView, RecentTripsView, RoutePlannerView, reverse_geocode, AllTripsView
)


urlpatterns = [
    path('hours-of-service/current/', CurrentHoursView.as_view(), name='current-hours'),
    path('trips/recent/', RecentTripsView.as_view(), name='recent-trips'),
    path('routes/plan/', RoutePlannerView.as_view(), name='plan-route'),
    path('trips/all/', AllTripsView.as_view(), name='all-trips'),
    path('geocode/reverse/', reverse_geocode, name='reverse-geocode'),
]