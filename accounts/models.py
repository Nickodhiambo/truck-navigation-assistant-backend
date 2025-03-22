from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    driver_license = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'
