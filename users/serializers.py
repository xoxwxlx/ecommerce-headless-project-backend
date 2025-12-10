from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import VendorCompany, Address, PasswordResetToken
import re

User = get_user_model()


class VendorCompanySerializer(serializers.ModelSerializer):
    """
    Serializer for VendorCompany model (list of available companies).
    """
    class Meta:
        model = VendorCompany
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class VendorRegistrationSerializer(serializers.Serializer):
    """
    Serializer for vendor registration with company access code.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    company_id = serializers.IntegerField(required=True)
    company_access_code = serializers.CharField(write_only=True, required=True, max_length=100)
    
    def validate(self, attrs):
        """
        Validate passwords match and company access code is correct.
        """
        # Check if passwords match
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Hasła nie są identyczne."})
        
        # Check if company exists and is active
        try:
            company = VendorCompany.objects.get(id=attrs['company_id'], is_active=True)
        except VendorCompany.DoesNotExist:
            raise serializers.ValidationError({"company_id": "Wybrana firma nie istnieje lub jest nieaktywna."})
        
        # Verify access code
        if not company.verify_access_code(attrs['company_access_code']):
            raise serializers.ValidationError({"company_access_code": "Nieprawidłowe hasło dostępu dla tej firmy."})
        
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Ten adres email jest już zarejestrowany."})
        
        attrs['company'] = company
        return attrs
    
    def create(self, validated_data):
        """
        Create a new vendor user.
        """
        company = validated_data.pop('company')
        validated_data.pop('password_confirm')
        validated_data.pop('company_id')
        validated_data.pop('company_access_code')
        
        password = validated_data.pop('password')
        
        user = User(
            email=validated_data['email'],
            role='vendor',
            vendor_company=company
        )
        user.set_password(password)
        user.save()
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the CustomUser model.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'role', 'vendor_company', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']
    
    def create(self, validated_data):
        """
        Create a new user with encrypted password.
        """
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """
        Update user instance, handling password encryption if provided.
        """
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm']
    
    def validate(self, attrs):
        """
        Validate that passwords match.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """
        Create a new user after removing password_confirm field.
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile management.
    Email is read-only, other fields can be updated.
    """
    email = serializers.EmailField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'date_joined']
        read_only_fields = ['id', 'email', 'date_joined']
    
    def validate_phone(self, value):
        """
        Validate phone number format (Polish format preferred).
        """
        if value:
            # Remove spaces and dashes
            cleaned = value.replace(' ', '').replace('-', '').replace('+', '')
            # Check if contains only digits (optionally starts with +)
            if not re.match(r'^[\d\+\s\-]+$', value):
                raise serializers.ValidationError("Numer telefonu może zawierać tylko cyfry, spacje, myślniki i znak +")
            # Check length (9 digits for Polish numbers, or 11-15 with country code)
            if len(cleaned) < 9 or len(cleaned) > 15:
                raise serializers.ValidationError("Numer telefonu musi zawierać od 9 do 15 cyfr")
        return value


class AddressSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery addresses.
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Address
        fields = ['id', 'user', 'recipient_name', 'street', 'postal_code', 
                  'city', 'country', 'phone', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_recipient_name(self, value):
        """
        Validate recipient name is not empty and has reasonable length.
        """
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Imię i nazwisko odbiorcy musi zawierać co najmniej 2 znaki")
        if len(value) > 200:
            raise serializers.ValidationError("Imię i nazwisko odbiorcy jest za długie")
        return value.strip()
    
    def validate_postal_code(self, value):
        """
        Validate Polish postal code format (XX-XXX).
        """
        if value:
            cleaned = value.replace(' ', '').replace('-', '')
            if not re.match(r'^\d{5}$', cleaned):
                raise serializers.ValidationError("Kod pocztowy musi być w formacie XX-XXX (np. 00-950)")
            # Format to XX-XXX
            if '-' not in value:
                value = f"{cleaned[:2]}-{cleaned[2:]}"
        return value
    
    def validate_phone(self, value):
        """
        Validate phone number format.
        """
        if value:
            cleaned = value.replace(' ', '').replace('-', '').replace('+', '')
            if not re.match(r'^[\d\+\s\-]+$', value):
                raise serializers.ValidationError("Numer telefonu może zawierać tylko cyfry, spacje, myślniki i znak +")
            if len(cleaned) < 9 or len(cleaned) > 15:
                raise serializers.ValidationError("Numer telefonu musi zawierać od 9 do 15 cyfr")
        return value
    
    def validate_street(self, value):
        """
        Validate street address is not empty.
        """
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Ulica i numer muszą zawierać co najmniej 3 znaki")
        return value.strip()
    
    def validate_city(self, value):
        """
        Validate city name is not empty.
        """
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Nazwa miasta musi zawierać co najmniej 2 znaki")
        return value.strip()


class ForgotPasswordSerializer(serializers.Serializer):
    """
    Serializer for forgot password request.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """
        Normalize email.
        """
        return value.lower().strip()


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for password reset with token.
    """
    token = serializers.UUIDField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        """
        Validate passwords match and token is valid.
        """
        # Check if passwords match
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Hasła nie są identyczne."})
        
        # Check if token exists and is valid
        try:
            token_obj = PasswordResetToken.objects.get(token=attrs['token'])
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Nieprawidłowy token resetowania hasła."})
        
        # Check if token is valid (not used and not expired)
        if not token_obj.is_valid():
            if token_obj.is_used:
                raise serializers.ValidationError({"token": "Ten token został już użyty."})
            else:
                raise serializers.ValidationError({"token": "Token wygasł. Poproś o nowy link resetowania hasła."})
        
        attrs['token_obj'] = token_obj
        return attrs
    
    def validate_password(self, value):
        """
        Validate password strength.
        """
        if len(value) < 8:
            raise serializers.ValidationError("Hasło musi zawierać co najmniej 8 znaków.")
        
        # Optional: Add more password strength requirements
        # if not re.search(r'[A-Z]', value):
        #     raise serializers.ValidationError("Hasło musi zawierać co najmniej jedną wielką literę.")
        # if not re.search(r'[a-z]', value):
        #     raise serializers.ValidationError("Hasło musi zawierać co najmniej jedną małą literę.")
        # if not re.search(r'[0-9]', value):
        #     raise serializers.ValidationError("Hasło musi zawierać co najmniej jedną cyfrę.")
        
        return value
