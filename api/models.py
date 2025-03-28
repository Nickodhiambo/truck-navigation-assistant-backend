from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Trip(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'scheduled'),
        ('ACTIVE', 'active'),
        ('COMPLETED', 'completed'),
        ('CANCELLED', 'cancelled')
    ]

    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    distance = models.FloatField(help_text="Distance in miles")
    estimated_hours = models.FloatField(help_text="Estimated driving hours")
    status = models.CharField(max_length=20, default='SCHEDULED', choices=STATUS_CHOICES)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.pickup_location} to {self.dropoff_location}'
    

class TripStop(models.Model):
    STOP_TYPES = [
        ('pickup', 'Pickup'),
        ('dropoff', 'Dropoff'),
        ('rest', 'Rest Stop'),
        ('fuel', 'Rest fuel')
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stop')
    type = models.CharField(max_length=10, choices=STOP_TYPES)
    location = models.CharField(max_length=255)
    arrival_time = models.CharField(max_length=50)
    duration = models.FloatField(help_text="Duration in hrs")
    coordinates = models.CharField(max_length=100, default=1)

    def __str__(self):
        return f'{self.type} at {self.location}'
    

class HoursOfService(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hours_of_service')
    date = models.DateField()
    
    # Hours used in specific periods
    cycle_used = models.FloatField(
        default=0.0, 
        help_text="Hours used in 70-hr/8 days cycle",
        validators=[MinValueValidator(0), MaxValueValidator(70)]
    )
    daily_used = models.FloatField(
        default=0.0, 
        help_text="Hours used in 14-hr daily window",
        validators=[MinValueValidator(0), MaxValueValidator(14)]
    )
    driving_used = models.FloatField(
        default=0.0, 
        help_text="Hours used in 11-hr driving limit",
        validators=[MinValueValidator(0), MaxValueValidator(11)]
    )
    
    class Meta:
        unique_together = ['driver', 'date']
        verbose_name_plural = "Hours of Service"
    
    def is_over_daily_limit(self):
        """Check if daily driving or duty hours exceed limits"""
        return (
            self.driving_used > 11 or 
            self.daily_used > 14
        )
    
    def is_over_cycle_limit(self):
        """Check if 70-hr/8-day cycle limit is exceeded"""
        return self.cycle_used > 70
    
    def __str__(self):
        return f'{self.driver.username} - {self.date}'
    

# class HoursOfService(models.Model):
#     driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hours_of_service')
#     date = models.DateField()
#     cycle_used = models.FloatField(
#         default=0.0, help_text="Hours used in 70-hr/8 days cycle")
#     daily_used = models.FloatField(
#         default=0.0, help_text="Hours used in 14-hr daily window"
#     )
#     driving_used = models.FloatField(
#         default=0.0, help_text="Hours used in 11-hr driving limit"
#     )

#     class Meta:
#         unique_together = ['driver', 'date']

#     def __str__(self):
#         return f'{self.driver.username} - {self.date}'
    

class LogSheet(models.Model):
    STATUS_CHOICES =[
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'submitted'),
        ('APPROVED', 'approved')
    ]

    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='log_sheets')
    trip = models.ForeignKey(
        Trip, on_delete=models.SET_NULL, blank=True, null=True, related_name="log_sheets")
    date = models.DateField()
    hours_logged = models.FloatField(help_text="Total hours logged for this day")
    cycle_hours = models.FloatField(help_text="Accumilated cycle hours")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add="True")

    class Meta:
        unique_together = ['driver', 'date']

    @property
    def trip_description(self):
        if self.trip:
            return f'{self.trip.pickup_location} to {self.trip.dropoff_location}'
        return None
    
    def __str__(self):
        return f'{self.driver.username} - {self.date}'
    

class LogActivity(models.Model):
    ACTIVITY_TYPES = [
        ('Driving', 'Driving'),
        ('ON_DUTY', 'On Duty Not Driving'),
        ('OFF_DUTY', 'Off duty'),
        ('SLEEPER', 'Sleeper Bearth'),
    ]

    log_sheet = models.ForeignKey(LogSheet, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    start_time = models.CharField(max_length=10)
    end_time = models.CharField(max_length=10)
    description = models.CharField(max_length=255)
    location = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.activity_type}: {self.start_time} to {self.end_time}'
