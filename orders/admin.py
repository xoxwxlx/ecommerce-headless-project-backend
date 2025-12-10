from django.contrib import admin
from .models import Order, OrderItem, GuestOrderAddress


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']


class GuestOrderAddressInline(admin.StackedInline):
    model = GuestOrderAddress
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_customer', 'order_type', 'total_amount', 'payment_status', 'created_at']
    list_filter = ['order_type', 'payment_status', 'created_at']
    search_fields = ['id', 'user__email', 'guest_email', 'guest_first_name', 'guest_last_name']
    readonly_fields = ['created_at', 'updated_at', 'is_paid']
    inlines = [OrderItemInline, GuestOrderAddressInline]
    
    def get_customer(self, obj):
        if obj.order_type == 'guest':
            return f"{obj.guest_first_name} {obj.guest_last_name} ({obj.guest_email})"
        return obj.user.email if obj.user else "---"
    get_customer.short_description = 'Klient'
    
    fieldsets = (
        ('Typ zamówienia', {
            'fields': ('order_type',)
        }),
        ('Użytkownik zarejestrowany', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
        ('Dane gościa', {
            'fields': ('guest_email', 'guest_first_name', 'guest_last_name', 'guest_phone'),
            'classes': ('collapse',)
        }),
        ('Szczegóły zamówienia', {
            'fields': ('total_amount', 'payment_status', 'is_paid')
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(GuestOrderAddress)
class GuestOrderAddressAdmin(admin.ModelAdmin):
    list_display = ['order', 'recipient_name', 'city', 'postal_code']
    search_fields = ['recipient_name', 'city', 'street', 'order__id']
    list_filter = ['country', 'city']
