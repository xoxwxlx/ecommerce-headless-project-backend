from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid
from datetime import timedelta


class VendorCompany(models.Model):
    """
    Model representing a vendor company with access credentials.
    """
    name = models.CharField(max_length=255, unique=True)
    access_code = models.CharField(max_length=100, help_text="Hasło dostępu dla rejestracji dostawcy")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'firma dostawcy'
        verbose_name_plural = 'firmy dostawców'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def verify_access_code(self, code):
        """Verify if provided access code matches."""
        return self.access_code == code


class CustomUserManager(BaseUserManager):
    """
    Manager for custom user model with email as the unique identifier.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        if not email:
            raise ValueError('Email field is required')
        
        email = self.normalize_email(email)
        extra_fields.setdefault('role', 'user')
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        """
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with email as the unique identifier.
    """
    ROLE_CHOICES = [
        ('user', 'Użytkownik'),
        ('vendor', 'Dostawca'),
        ('admin', 'Administrator'),
    ]
    
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    vendor_company = models.ForeignKey(VendorCompany, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendors')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'użytkownik'
        verbose_name_plural = 'użytkownicy'
    
    def __str__(self):
        return self.email


class Address(models.Model):
    """
    Model representing a delivery address for a user.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    recipient_name = models.CharField(max_length=200, verbose_name='Imię i nazwisko odbiorcy')
    street = models.CharField(max_length=255, verbose_name='Ulica i numer')
    postal_code = models.CharField(max_length=20, verbose_name='Kod pocztowy')
    city = models.CharField(max_length=100, verbose_name='Miasto')
    country = models.CharField(max_length=100, default='Polska', verbose_name='Kraj')
    phone = models.CharField(max_length=20, verbose_name='Numer telefonu')
    is_default = models.BooleanField(default=False, verbose_name='Adres domyślny')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'adres dostawy'
        verbose_name_plural = 'adresy dostawy'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.recipient_name} - {self.city}, {self.street}"
    
    def save(self, *args, **kwargs):
        """
        If this address is set as default, remove default flag from other addresses.
        """
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class PasswordResetToken(models.Model):
    """
    Model representing a password reset token for a user.
    """
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'token resetowania hasła'
        verbose_name_plural = 'tokeny resetowania hasła'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.email} - {'Used' if self.is_used else 'Active'}"
    
    def save(self, *args, **kwargs):
        """
        Set expiration time to 1 hour from creation if not set.
        """
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """
        Check if token is valid (not used and not expired).
        """
        return not self.is_used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        """
        Mark token as used.
        """
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
