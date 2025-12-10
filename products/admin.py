from django.contrib import admin
from .models import Product  # importujemy swój model

# rejestrujemy model w adminie
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'stock')
    search_fields = ('title', 'author')
    list_filter = ('created_at',)
    ordering = ('-created_at',)