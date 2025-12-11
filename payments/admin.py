from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'stripe_session_id', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__id', 'stripe_session_id', 'order__user__email']
    readonly_fields = ['created_at', 'updated_at', 'stripe_session_id']
    list_per_page = 25
    
    fieldsets = (
        ('Informacje o płatności', {
            'fields': ('order', 'amount', 'status'),
            'classes': ('wide',)
        }),
        ('Stripe', {
            'fields': ('stripe_session_id',),
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

