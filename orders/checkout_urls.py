from django.urls import path
from .guest_views import GuestCheckoutView

urlpatterns = [
    path('guest/', GuestCheckoutView.as_view(), name='guest-checkout'),
]
