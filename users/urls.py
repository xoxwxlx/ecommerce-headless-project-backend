from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, 
    LoginView, 
    MeView, 
    VendorRegisterView, 
    VendorCompanyListView,
    UserProfileView,
    AddressListCreateView,
    AddressDetailView,
    AddressSetDefaultView,
    ForgotPasswordView,
    ResetPasswordView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', MeView.as_view(), name='me'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password reset
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    
    # Vendor registration
    path('vendor/companies/', VendorCompanyListView.as_view(), name='vendor-companies'),
    path('vendor/register/', VendorRegisterView.as_view(), name='vendor-register'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Addresses
    path('addresses/', AddressListCreateView.as_view(), name='address-list-create'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),
    path('addresses/<int:pk>/default/', AddressSetDefaultView.as_view(), name='address-set-default'),
]
