from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login
from .serializers import (
    DriverRegistrationSerializer, UserSerializer, LoginSerializer
)

class DriverRegistrationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer =DriverRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {"message": "Driver registered successfully",
                 "token": token.key,
                 "user": UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email =  serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=email, password=password)
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                return Response(
                    {"message": "Logged in successfully",
                     "token": token.key,
                     "user": UserSerializer(user).data
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({"message": "Logged out successfully"})
        except Token.DoesNotExist:
            return Response(
                {"message": "Some error occurred"}, status=status.HTTP_400_BAD_REQUEST
            )
        
class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.data)
        return Response(serializer.data)