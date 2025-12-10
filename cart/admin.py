from django.contrib import admin
from .models import Cart, CartItem, GuestCart, GuestCartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['subtotal', 'added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_price', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at', 'total_price', 'total_items']
    inlines = [CartItemInline]


class GuestCartItemInline(admin.TabularInline):
    model = GuestCartItem
    extra = 0
    readonly_fields = ['subtotal', 'added_at']


@admin.register(GuestCart)
class GuestCartAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'total_items', 'total_price', 'created_at']
    search_fields = ['session_key']
    readonly_fields = ['created_at', 'updated_at', 'total_price', 'total_items']
    inlines = [GuestCartItemInline]
    list_filter = ['created_at']
