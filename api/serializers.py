from rest_framework import serializers
from .models import Trip, TripStop, HoursOfService, LogSheet, LogActivity

class TripStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripStop
        fields = ['id', 'type', 'location', 'arrival_time', 'duration']

class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ['id', 'pickup_location', 'dropoff_location', 'distance', 
                  'estimated_hours', 'status', 'start_time']

class TripDetailSerializer(serializers.ModelSerializer):
    stops = TripStopSerializer(many=True, read_only=True)
    
    class Meta:
        model = Trip
        fields = ['id', 'pickup_location', 'dropoff_location', 'distance', 
                  'estimated_hours', 'status', 'start_time', 'end_time', 'stops']

class HoursOfServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoursOfService
        fields = ['id', 'date', 'cycle_used', 'daily_used', 'driving_used']

class LogActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogActivity
        fields = ['id', 'type', 'start_time', 'end_time', 'description', 'location']

class LogSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogSheet
        fields = ['id', 'date', 'trip_description', 'hours_logged', 'status']

class LogSheetDetailSerializer(serializers.ModelSerializer):
    activities = LogActivitySerializer(many=True, read_only=True)
    
    class Meta:
        model = LogSheet
        fields = ['id', 'date', 'trip_description', 'hours_logged', 
                  'cycle_hours', 'status', 'activities']
        
# class CurrentHoursSerializer(serializers.Serializer):
#     driving_used = serializers.FloatField()
#     daily_used = serializers.FloatField()

# class RouteRequestSerializer(serializers.Serializer):
#     current_location = serializers.CharField()
#     pickup_location = serializers.CharField()
#     dropoff_location = serializers.CharField()
#     current_hours = CurrentHoursSerializer()
class RouteRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)

class RouteResponseSerializer(serializers.Serializer):
    total_distance = serializers.FloatField()
    driving_hours = serializers.FloatField()
    total_hours = serializers.FloatField()
    required_stops = serializers.IntegerField()
    stops = TripStopSerializer(many=True)

class GeocodingRequestSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()