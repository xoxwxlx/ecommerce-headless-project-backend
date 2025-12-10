from django.urls import path
from .views import AddToCartView, CartView, RemoveFromCartView
from .guest_views import (
    GuestCartView,
    AddToGuestCartView,
    UpdateGuestCartItemView,
    RemoveFromGuestCartView,
    ClearGuestCartView
)

urlpatterns = [
    # Authenticated user cart
    path('add/', AddToCartView.as_view(), name='add-to-cart'),
    path('', CartView.as_view(), name='cart'),
    path('remove/<int:pk>/', RemoveFromCartView.as_view(), name='remove-from-cart'),
    
    # Guest cart
    path('guest/', GuestCartView.as_view(), name='guest-cart'),
    path('guest/add/', AddToGuestCartView.as_view(), name='add-to-guest-cart'),
    path('guest/update/<int:pk>/', UpdateGuestCartItemView.as_view(), name='update-guest-cart-item'),
    path('guest/remove/<int:pk>/', RemoveFromGuestCartView.as_view(), name='remove-from-guest-cart'),
    path('guest/clear/', ClearGuestCartView.as_view(), name='clear-guest-cart'),
]
