from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, VendorCompany, Address, PasswordResetToken
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    VendorRegistrationSerializer,
    VendorCompanySerializer,
    UserProfileSerializer,
    AddressSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)


class VendorCompanyListView(generics.ListAPIView):
    """
    API endpoint to list available vendor companies for registration.
    GET /api/users/vendor/companies/
    """
    queryset = VendorCompany.objects.filter(is_active=True)
    serializer_class = VendorCompanySerializer
    permission_classes = [permissions.AllowAny]


class VendorRegisterView(generics.CreateAPIView):
    """
    API endpoint for vendor registration.
    POST /api/users/vendor/register/
    """
    serializer_class = VendorRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'vendor_company': user.vendor_company.name if user.vendor_company else None
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Konto dostawcy zostało pomyślnie utworzone.'
        }, status=status.HTTP_201_CREATED)


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    API endpoint for user login.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    API endpoint to get current authenticated user data.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for user profile management.
    GET /api/user/profile - Get user profile data
    PATCH /api/user/profile - Update user profile data
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class AddressListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating addresses.
    GET /api/user/addresses - List all user addresses
    POST /api/user/addresses - Create new address
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for managing individual addresses.
    GET /api/user/addresses/:id - Get address details
    PATCH /api/user/addresses/:id - Update address
    DELETE /api/user/addresses/:id - Delete address
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only allow access to user's own addresses
        return Address.objects.filter(user=self.request.user)


class AddressSetDefaultView(APIView):
    """
    API endpoint to set an address as default.
    PATCH /api/user/addresses/:id/default
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, pk):
        try:
            address = Address.objects.get(pk=pk, user=request.user)
        except Address.DoesNotExist:
            return Response(
                {'error': 'Adres nie został znaleziony lub nie należy do Ciebie'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Set this address as default (model's save method handles removing default from others)
        address.is_default = True
        address.save()
        
        serializer = AddressSerializer(address)
        return Response({
            'message': 'Adres został ustawiony jako domyślny',
            'address': serializer.data
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """
    API endpoint for forgot password request.
    POST /api/auth/forgot-password
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        # Always return the same message regardless of whether email exists
        # This prevents user enumeration attacks
        success_message = "Jeśli konto z tym adresem email istnieje, wysłaliśmy link do resetowania hasła."
        
        try:
            user = CustomUser.objects.get(email=email)
            
            # Invalidate all previous unused tokens for this user
            PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Create new reset token
            reset_token = PasswordResetToken.objects.create(user=user)
            
            # Send email with reset link
            self.send_reset_email(user, reset_token)
            
        except CustomUser.DoesNotExist:
            # Don't reveal that the email doesn't exist
            pass
        
        return Response({
            'message': success_message
        }, status=status.HTTP_200_OK)
    
    def send_reset_email(self, user, reset_token):
        """
        Send password reset email to user.
        """
        # Get frontend URL from settings or use default
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{frontend_url}/reset-password?token={reset_token.token}"
        
        subject = 'Resetowanie hasła'
        message = f"""
Witaj,

Otrzymaliśmy prośbę o zresetowanie hasła do Twojego konta.

Aby ustawić nowe hasło, kliknij w poniższy link:
{reset_link}

Link jest ważny przez 1 godzinę.

Jeśli nie prosiłeś o reset hasła, zignoruj tę wiadomość.

Pozdrawiamy,
Zespół Księgarni
"""
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't reveal to user
            print(f"Error sending password reset email: {e}")


class ResetPasswordView(APIView):
    """
    API endpoint for password reset with token.
    POST /api/auth/reset-password
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get token object and new password
        token_obj = serializer.validated_data['token_obj']
        new_password = serializer.validated_data['password']
        
        # Update user password
        user = token_obj.user
        user.set_password(new_password)
        user.save()
        
        # Mark token as used
        token_obj.mark_as_used()
        
        # Send confirmation email
        try:
            self.send_confirmation_email(user)
        except Exception as e:
            # Log error but don't fail the reset
            print(f"Error sending confirmation email: {e}")
        
        return Response({
            'message': 'Hasło zostało pomyślnie zmienione. Możesz się teraz zalogować.'
        }, status=status.HTTP_200_OK)
    
    def send_confirmation_email(self, user):
        """
        Send password change confirmation email.
        """
        subject = 'Hasło zostało zmienione'
        message = f"""
Witaj,

Twoje hasło zostało pomyślnie zmienione.

Jeśli to nie Ty dokonałeś tej zmiany, natychmiast skontaktuj się z nami.

Pozdrawiamy,
Zespół Księgarni
"""
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
