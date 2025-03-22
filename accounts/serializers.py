from rest_framework import serializers
from django.contrib.auth.models import User
from .models import DriverProfile


class DriverRegistrationSerializer(serializers.ModelSerializer):
    driver_license = serializers.CharField(max_length=20)
    phone_number = serializers.CharField(max_length=15)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'password',
            'driver_license', 'phone_number'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        driver_license = validated_data.pop('driver_license')
        phone_number = validated_data.pop('phone_number')

        user = User.objects.create(
            first_name = validated_data['first_name'],
            last_name = validated_data['last_name'],
            email = validated_data['email'],
            username = validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()

        DriverProfile.objects.create(
            user=user,
            driver_license=driver_license,
            phone_number=phone_number
        )
        return user
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class LoginSerializer(serializers.Serializer):
    username = serializers.EmailField()
    password = serializers.CharField()
