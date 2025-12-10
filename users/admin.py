from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, VendorCompany, Address, PasswordResetToken


@admin.register(VendorCompany)
class VendorCompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'vendor_company', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informacje osobiste', {'fields': ('first_name', 'last_name', 'phone', 'role', 'vendor_company')}),
        ('Uprawnienia', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Ważne daty', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'phone', 'role', 'vendor_company', 'is_staff', 'is_active'),
        }),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['recipient_name', 'user', 'city', 'postal_code', 'is_default', 'created_at']
    list_filter = ['is_default', 'country', 'city', 'created_at']
    search_fields = ['recipient_name', 'city', 'street', 'user__email']
    ordering = ['-is_default', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Użytkownik', {'fields': ('user',)}),
        ('Dane odbiorcy', {'fields': ('recipient_name', 'phone')}),
        ('Adres', {'fields': ('street', 'postal_code', 'city', 'country')}),
        ('Ustawienia', {'fields': ('is_default',)}),
        ('Daty', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expires_at', 'is_used', 'is_valid_display']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['token', 'created_at', 'used_at']
    ordering = ['-created_at']
    
    def is_valid_display(self, obj):
        return obj.is_valid()
    is_valid_display.short_description = 'Ważny'
    is_valid_display.boolean = True
    
    fieldsets = (
        ('Użytkownik', {'fields': ('user',)}),
        ('Token', {'fields': ('token', 'is_used')}),
        ('Daty', {'fields': ('created_at', 'expires_at', 'used_at')}),
    )
