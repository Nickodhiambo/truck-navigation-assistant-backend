from django.urls import path
from .views import (
    DriverRegistrationView, LoginView, LogoutView, UserView
)


urlpatterns = [
    path('register/driver/', DriverRegistrationView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/', UserView.as_view(), name='user'),
]