# REST framework imports
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

# Django imports
import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

# My custom API imports
from .models import Trip, HoursOfService, LogSheet, TripStop, LogActivity
from .serializers import (
    TripSerializer, TripDetailSerializer, HoursOfServiceSerializer,
    LogSheetSerializer, LogSheetDetailSerializer, RouteRequestSerializer,
    RouteResponseSerializer, GeocodingRequestSerializer
)
from accounts.models import DriverProfile

# Third part API imports
import datetime
import math
import requests
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
from datetime import timedelta
from geopy.geocoders import Nominatim
    
        


class CurrentHoursView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get today's hours or create default entry
        today = datetime.date.today()
        hours, created = HoursOfService.objects.get_or_create(
            driver=request.user,
            date=today,
            defaults={
                'cycle_used': 0, 
                'daily_used': 0,
                'driving_used': 0
            }
        )
        serializer = HoursOfServiceSerializer(hours)
        return Response(serializer.data)
    

class RecentTripsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get 5 most recent trips
        trips = Trip.objects.filter(driver=request.user).order_by('-created_at')[:5]
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)

class AllTripsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        trip_details = Trip.objects.filter(driver=request.user).order_by('-created_at')
        serializer = TripSerializer(trip_details, many=True)
        return Response(serializer.data)
        
class RoutePlannerView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = RouteRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Get validated data
            current_location = serializer.validated_data['current_location']
            pickup_location = serializer.validated_data['pickup_location']
            dropoff_location = serializer.validated_data['dropoff_location']
            
            # Retrieve current hours of service for the driver
            current_hours = HoursOfService.objects.get(
                driver=request.user, 
                date=datetime.date.today()
            )
            
            # Call the mapping API and calculate the route
            route_data = self._calculate_route(
                current_location, 
                pickup_location, 
                dropoff_location, 
                current_hours
            )

            # Log trip details to database
            trip = Trip.objects.create(
                driver = request.user,
                pickup_location = pickup_location,
                dropoff_location = dropoff_location,
                estimated_hours = route_data['total_hours'],
                distance = route_data['total_distance']
            )

            trip.save()

            cycle_hours = current_hours.cycle_used + route_data['total_hours']

            # Create a logsheet instance to receive trip activity information
            logsheet = LogSheet.objects.create(
                driver=request.user,
                trip = trip,
                date = datetime.date.today(),
                hours_logged = route_data['total_hours'],
                cycle_hours = cycle_hours,
            )

            logsheet.save()

            stops = route_data['stops']
            for stop in stops:
                activity = stop['activity']
                start_time, end_time = stop['arrival_time'], stop['departure_time']
                location, type = stop['location'], stop['type']
            
                # Log activity on sheet
                log_activity = LogActivity.objects.create(
                    log_sheet=logsheet,
                    activity_type = activity,
                    location = location,
                    description = type,
                    start_time=start_time,
                    end_time=end_time
                )

                log_activity.save()

            # Update hours of service after route calculation
            self._update_hours_of_service(
                current_hours, 
                route_data['driving_hours'], 
                route_data['total_hours']
            )
            
            response_serializer = RouteResponseSerializer(route_data)
            return Response(response_serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _update_hours_of_service(self, hours_of_service, driving_hours, total_hours):
        """
        Update driver's hours of service after trip planning
        """
        # Update driving hours used
        hours_of_service.driving_used += driving_hours
        
        # Update daily duty hours
        hours_of_service.daily_used += total_hours
        
        # Update cycle hours (70-hr/8-day cycle)
        hours_of_service.cycle_used += total_hours
        
        # Save updated hours
        hours_of_service.save()
    
    def _calculate_route(self, current_location, pickup_location, dropoff_location, current_hours):
        """
        Calculate a route using OSRM with HOS compliance
        
        Args:
            current_location (str): Current driver location
            pickup_location (str): Cargo pickup location
            dropoff_location (str): Cargo dropoff location 
            current_hours (dict): Current driver's hours of service
        
        Returns:
            dict: Route details including stops, distances, and times
        """
        
        # Initialize geocoder for converting addresses to coordinates
        geolocator = Nominatim(user_agent="trucking_route_planner")
        
        # Convert addresses to coordinates
        try:
            current_coords = self._geocode_location(geolocator, current_location)
            pickup_coords = self._geocode_location(geolocator, pickup_location)
            dropoff_coords = self._geocode_location(geolocator, dropoff_location)
        except Exception as e:
            # Handle geocoding errors
            raise ValueError(f"Geocoding error: {str(e)}")
        
        # Get route from current location to pickup
        to_pickup_route = self._get_osrm_route(current_coords, pickup_coords)
        
        # Get route from pickup to dropoff
        pickup_to_dropoff_route = self._get_osrm_route(pickup_coords, dropoff_coords)
        
        # Extract distances and durations
        to_pickup_distance = to_pickup_route['distance'] / 1609.34  # Convert meters to miles
        to_pickup_duration = to_pickup_route['duration'] / 3600  # Convert seconds to hours
        
        pickup_to_dropoff_distance = pickup_to_dropoff_route['distance'] / 1609.34
        pickup_to_dropoff_duration = pickup_to_dropoff_route['duration'] / 3600
        
        total_distance = to_pickup_distance + pickup_to_dropoff_distance
        total_driving_duration = to_pickup_duration + pickup_to_dropoff_duration
        
        # HOS compliance calculations
        # Current hours already used
        current_driving_used = current_hours.driving_used
        current_duty_used = current_hours.daily_used
        
        # HOS limits
        max_driving_hours = 11  # Maximum 11 hours driving time
        max_duty_hours = 14     # Maximum 14 hours on duty
        break_required_after = 8  # Break required after 8 hours of driving
        remaining_driving_hours = max_driving_hours - current_driving_used
        remaining_duty_hours = max_duty_hours - current_duty_used
        
        # Generate stops with locations based on HOS regulations
        stops = []
        
        # Start time is now
        from datetime import datetime
        current_time = datetime.now()
        
        # Add current location as starting point
        stops.append({
            'type': 'start',
            'location': current_location,
            'coordinates': self._geocode_location(geolocator, current_location),
            'arrival_time': current_time.strftime('%I:%M %p'),
            'departure_time': current_time.strftime('%I:%M %p'),
            'duration': 0,
            'activity': 'OFF_DUTY'
        })

        
        # Calculate drive to pickup
        current_driving_segment = to_pickup_duration
        
        # Check if we need a break before reaching pickup
        if current_driving_used + current_driving_segment > break_required_after:
            # Time until break is needed
            driving_until_break = break_required_after - current_driving_used
            # Calculate where the break would occur
            break_ratio = driving_until_break / current_driving_segment
            break_distance = to_pickup_distance * break_ratio
            
            # Find a rest stop location along the route
            break_location = self._find_rest_stop_along_route(
                to_pickup_route, 
                break_ratio
            )
            
            # Add drive time to current time
            current_time += timedelta(hours=driving_until_break)
            
            # Add break stop
            stops.append({
                'type': 'rest',
                'location': break_location,
                'coordinates': self._geocode_location(geolocator, break_location),
                'arrival_time': current_time.strftime('%I:%M %p'),
                'departure_time': (current_time + timedelta(minutes=30)).strftime('%I:%M %p'),
                'duration': 0.5,
                'activity': 'ON_DUTY'
            })
            
            # Update times
            current_time += timedelta(minutes=30)
            current_driving_used = 0  # Reset driving hours after break
            current_driving_segment -= driving_until_break
        
        # Update driving hours
        current_driving_used += current_driving_segment
        
        # Update current time after driving to pickup
        current_time += timedelta(hours=current_driving_segment)
        
        # Add pickup stop
        stops.append({
            'type': 'pickup',
            'location': pickup_location,
            'coordinates': self._geocode_location(geolocator, pickup_location),
            'arrival_time': current_time.strftime('%I:%M %p'),
            'departure_time': (current_time + timedelta(hours=1)).strftime('%I:%M %p'),
            'duration': 1.0,
            'activity': 'ON_DUTY'
        })
        
        # Update current time after pickup
        current_time += timedelta(hours=1)
        
        # Check if we need to take a 10-hour rest
        if current_duty_used + to_pickup_duration + 1 > max_duty_hours:
            stops.append({
                'type': 'overnight',
                'location': pickup_location,
                'coordinates': self._geocode_location(geolocator, pickup_location),
                'arrival_time': current_time.strftime('%I:%M %p'),
                'departure_time': (current_time + timedelta(hours=10)).strftime('%I:%M %p'),
                'duration': 10.0,
                'activity': 'SLEEPER'
            })
            current_time += timedelta(hours=10)
            current_driving_used = 0
            current_duty_used = 0
        else:
            current_duty_used += to_pickup_duration + 1
        
        # Calculate rest stops for the route from pickup to dropoff
        remaining_distance = pickup_to_dropoff_distance
        remaining_duration = pickup_to_dropoff_duration
        
        while remaining_distance > 0:
            # Calculate how far we can drive before next break
            if current_driving_used >= break_required_after:
                # Need a break now
                driving_segment = 0
            else:
                driving_segment = min(
                    break_required_after - current_driving_used,  # Time until break
                    remaining_duration,  # Remaining drive time
                    max_duty_hours - current_duty_used  # Time until end of duty
                )
            
            # If we can't drive any further, take a break
            if driving_segment == 0:
                ratio_driven = 1 - (remaining_distance / pickup_to_dropoff_distance)
                rest_location = self._find_rest_stop_along_route(
                    pickup_to_dropoff_route, 
                    ratio_driven
                )
                
                stops.append({
                    'type': 'rest',
                    'location': rest_location,
                    'coordinates': self._geocode_location(geolocator, rest_location),
                    'arrival_time': current_time.strftime('%I:%M %p'),
                    'departure_time': (current_time + timedelta(minutes=30)).strftime('%I:%M %p'),
                    'duration': 0.5,
                    'activity': 'ON_DUTY'
                })
                
                current_time += timedelta(minutes=30)
                current_driving_used = 0
                continue
                
            # If we need an overnight rest due to duty hours
            if current_duty_used + driving_segment + 0.5 >= max_duty_hours:
                ratio_driven = 1 - (remaining_distance / pickup_to_dropoff_distance)
                rest_location = self._find_rest_stop_along_route(
                    pickup_to_dropoff_route, 
                    ratio_driven
                )
                
                stops.append({
                    'type': 'overnight',
                    'location': rest_location,
                    'coordinates': self._geocode_location(geolocator, rest_location),
                    'arrival_time': current_time.strftime('%I:%M %p'),
                    'departure_time': (current_time + timedelta(hours=10)).strftime('%I:%M %p'),
                    'duration': 10.0,
                    'activity': 'SLEEPER'
                })
                
                current_time += timedelta(hours=10)
                current_driving_used = 0
                current_duty_used = 0
                continue
            
            # Drive for the segment
            drive_segment_distance = (driving_segment / remaining_duration) * remaining_distance
            
            # Update counters
            current_time += timedelta(hours=driving_segment)
            current_driving_used += driving_segment
            current_duty_used += driving_segment
            remaining_distance -= drive_segment_distance
            remaining_duration -= driving_segment
            
            # Check for fuel stop (roughly every 1000 miles)
            driven_distance = total_distance - remaining_distance
            if int(driven_distance / 1000) != int((driven_distance - drive_segment_distance) / 1000):
                ratio_driven = 1 - (remaining_distance / pickup_to_dropoff_distance)
                fuel_location = self._find_fuel_stop_along_route(
                    pickup_to_dropoff_route, 
                    ratio_driven
                )
                
                stops.append({
                    'type': 'fuel',
                    'location': fuel_location,
                    'coordinates': self._geocode_location(geolocator, fuel_location),
                    'arrival_time': current_time.strftime('%I:%M %p'),
                    'departure_time': (current_time + timedelta(minutes=15)).strftime('%I:%M %p'),
                    'duration': 0.25,
                    'activity': 'ON_DUTY'
                })
                
                current_time += timedelta(minutes=15)
                current_duty_used += 0.25
            
            # If we've completed the route
            if remaining_distance <= 0:
                break
        
        # Add dropoff stop
        stops.append({
            'type': 'dropoff',
            'location': dropoff_location,
            'coordinates': self._geocode_location(geolocator, dropoff_location),
            'arrival_time': current_time.strftime('%I:%M %p'),
            'departure_time': (current_time + timedelta(hours=1)).strftime('%I:%M %p'),
            'duration': 1.0,
            'activity': 'ON_DUTY'
        })
        
        # Calculate total trip time
        first_stop_time = datetime.strptime(stops[0]['arrival_time'], '%I:%M %p')
        last_stop_time = datetime.strptime(stops[-1]['departure_time'], '%I:%M %p')
        
        # Handle date crossing
        if last_stop_time < first_stop_time:
            # Add a day
            last_stop_time = last_stop_time + timedelta(days=1)
        
        total_trip_time = (last_stop_time - first_stop_time).total_seconds() / 3600

        
        return {
            'total_distance': round(total_distance, 1),
            'driving_hours': round(total_driving_duration, 1),
            'total_hours': round(total_trip_time, 1),
            'required_stops': len(stops) - 2,  # Exclude start and end
            'stops': stops,
        }
    
    def _geocode_location(self, geolocator, location_name):
        """
        Convert address to coordinates
        
        Args:
            geolocator: Nominatim geolocator instance
            location_name (str): Address or location name
            
        Returns:
            tuple: (longitude, latitude)
        """
        location = geolocator.geocode(location_name)
        if not location:
            raise ValueError(f"Could not geocode location: {location_name}")
        return f"{location.longitude},{location.latitude}"
    
    def _get_osrm_route(self, start_coords, end_coords):
        """
        Get route from OSRM
        
        Args:
            start_coords (str): Start coordinates "lon,lat"
            end_coords (str): End coordinates "lon,lat"
            
        Returns:
            dict: Route information
        """
        # Using a public OSRM instance
        base_url = "https://router.project-osrm.org/route/v1/driving/"
        url = f"{base_url}{start_coords};{end_coords}?overview=full&alternatives=false&steps=true"
       
        
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"OSRM API error: {response.status_code}")
        
        data = response.json()
        if data['code'] != 'Ok':
            raise Exception(f"Routing error: {data['code']}")
        
        route = data['routes'][0]
        return route
    
    def _find_rest_stop_along_route(self, route, ratio):
        """
        Find a rest stop along the route at approximately the given ratio of the journey
        
        Args:
            route (dict): OSRM route response
            ratio (float): Route completion ratio (0-1)
            
        Returns:
            str: Description of a rest stop location
        """
        # Will use POI data to find actual rest stops in future versions
        # For now, estimate location based on route geometry
        steps = route.get('legs', [{}])[0].get('steps', [])
        
        # Find the step that corresponds roughly to the ratio
        current_distance = 0
        target_distance = route['distance'] * ratio
        step_location = "Rest Area"
        
        for step in steps:
            current_distance += step['distance']
            if current_distance >= target_distance:
                # Extract a location name from the step instructions
                instruction = step.get('maneuver', {}).get('location', [])
                if instruction:
                    long = instruction[0]
                    lat = instruction[1]

                    geolocator = Nominatim(user_agent="trucking_route_planner")
                    location = geolocator.reverse(f'{lat}, {long}')
                    address = location.address

                    step_location = address
                break
        
        return step_location
    
    def _find_fuel_stop_along_route(self, route, ratio):
        """
        Find a fuel stop along the route at approximately the given ratio of the journey
        
        Args:
            route (dict): OSRM route response
            ratio (float): Route completion ratio (0-1)
            
        Returns:
            str: Description of a fuel stop location
        """
        # Similar to finding rest stops, but looking for gas stations
        # In production, you would use OSM or Overpass API to find actual gas stations
        steps = route.get('legs', [{}])[0].get('steps', [])
        
        # Find the step that corresponds roughly to the ratio
        current_distance = 0
        target_distance = route['distance'] * ratio
        step_location = "Fuel Station"
        
        for step in steps:
            current_distance += step['distance']
            if current_distance >= target_distance:
                instruction = step.get('maneuver', {}).get('location', [])
                if instruction:
                    long = instruction[0]
                    lat = instruction[1]

                    geolocator = Nominatim(user_agent="trucking_route_planner")
                    location = geolocator.reverse(f'{lat}, {long}')
                    address = location.address
                    
                    step_location = address
                break
        
        return step_location
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reverse_geocode(request):
    serializer = GeocodingRequestSerializer(data=request.query_params)
    if serializer.is_valid():
        lat =  serializer.validated_data['lat']
        lng = serializer.validated_data['lng']

        geolocator = Nominatim(user_agent="trucking_route_planner")
        location = geolocator.reverse(f'{lat}, {lng}')
        address = location.address
        return Response(
            {'formatted_address': address}
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def generate_driver_log_pdf(request):
    try:
        # Get the driver log data
        from datetime import datetime
        driver_log = LogSheet.objects.get(date=datetime.today())
        activities = driver_log.activities.all()
        
        # Create a buffer for the PDF
        buffer = io.BytesIO()
        
        # Get the absolute path to your PDF template
        template_path = os.path.join(settings.BASE_DIR, 'static', 'pdf_templates', 'blank-paper-log.pdf')
        
        # Check if file exists
        if not os.path.exists(template_path):
            return Response({'error': 'PDF template not found'}, status=404)
        
        # Open the template PDF
        template_pdf = PdfReader(open(template_path, 'rb'))
        output_pdf = PdfWriter()
        
        # Get the first page of the template
        template_page = template_pdf.pages[0]
        output_pdf.add_page(template_page)

        # Create a new PDF with ReportLab to overlay data
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=letter)

        driver = DriverProfile.objects.get(
            user=request.driver
        )

        c.drawString(233.2, 131.0, driver_log.date.strftime('%m/%d/%Y'))
        c.drawString(117.6, 165.7, driver_log.trip.pickup_location)
        c.drawString(331.5, 167.7, driver_log.trip.dropoff_location)
        c.drawString(206.2, 204.3, driver_log.trip.distance)
        c.drawString(113.7, 248.6, driver.driver_license)

        # Define grid parameters according to the blank log
        grid_start_x = 73.2  # Left edge of grid
        grid_start_y = 412.4 # Bottom edge of grid
        grid_width = 454.9   # Total width of the 24-hour grid
        grid_height = 19.2  # Total height of the activity grid

        # Define activity row positions (y-coordinates)
        activity_rows = {
            'OFF_DUTY': grid_start_y + grid_height * 0.8,
            'SLEEPER': grid_start_y + grid_height * 0.6,
            'Driving': grid_start_y + grid_height * 0.4,
            'ON_DUTY': grid_start_y + grid_height * 0.2,
        }

        # Function to convert 12-hour time string to x-coordinate
        def time_to_x_coord(time_str):
            try:
                # Handle different possible 12-hour formats
                if ':' in time_str:
                    # Format like "2:30 PM" or "10:45 AM"
                    time_parts = time_str.strip().split(' ')
                    hour_minute = time_parts[0].split(':')
                    hour = int(hour_minute[0])
                    minute = int(hour_minute[1]) if len(hour_minute) > 1 else 0
                    am_pm = time_parts[1].upper() if len(time_parts) > 1 else 'AM'
                else:
                    # Format like "2 PM" or "10 AM"
                    time_parts = time_str.strip().split(' ')
                    hour = int(time_parts[0])
                    minute = 0
                    am_pm = time_parts[1].upper() if len(time_parts) > 1 else 'AM'
                
                # Convert to 24-hour format
                if am_pm == 'PM' and hour < 12:
                    hour += 12
                elif am_pm == 'AM' and hour == 12:
                    hour = 0
                
                # Calculate position on 24-hour grid
                hour_fraction = hour + (minute / 60)
                x_position = grid_start_x + (hour_fraction / 24) * grid_width
                return x_position
            except (ValueError, IndexError):
                # Return default position if conversion fails
                print(f"Could not parse time: {time_str}")
                return grid_start_x
            
            # Draw activity lines
        for activity in activities:
            # Get y-coordinate for this activity type
            y_position = activity_rows.get(activity.activity_type, grid_start_y)
            
            # Get x-coordinates for start and end times
            start_x = time_to_x_coord(activity.start_time)
            end_x = time_to_x_coord(activity.end_time)
            
            # Set line properties
            c.setStrokeColorRGB(0, 0, 0)  # Black line
            c.setLineWidth(2)             # Line thickness
            
            # Draw the horizontal line
            c.line(start_x, y_position, end_x, y_position)
            
            # Draw small vertical markers at start and end (optional)
            c.line(start_x, y_position - 5, start_x, y_position + 5)
            c.line(end_x, y_position - 5, end_x, y_position + 5)
            
            # # Add activity description if space permits
            # if end_x - start_x > 50:  # Only add text if there's enough space
            #     c.setFont("Helvetica", 8)
            #     text_width = c.stringWidth(activity.description, "Helvetica", 8)
            #     if text_width < (end_x - start_x):
            #         c.drawString(start_x + 5, y_position + 8, activity.description)
            
            # # Add location text below the grid (optional)
            # if activity.location:
            #     c.setFont("Helvetica", 8)
            #     c.drawString(start_x, grid_start_y - 15, activity.location)
        
        c.save()
        
        # Merge the template with the overlay
        overlay_buffer.seek(0)
        overlay_pdf = PdfReader(overlay_buffer)
        template_page.merge_page(overlay_pdf.pages[0])
        
        # Write the output PDF to the response buffer
        output_pdf.write(buffer)
        buffer.seek(0)
        
        # Create response with PDF
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="driver_log_{log_id}.pdf"'
        
        return response
        
    except LogSheet.DoesNotExist:
        return Response({'error': 'Log sheet not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)