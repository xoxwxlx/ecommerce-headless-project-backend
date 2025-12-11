from django.contrib import admin
from .models import Product  # importujemy swój model

# rejestrujemy model w adminie
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'stock', 'format', 'publication_year')
    search_fields = ('title', 'author', 'isbn', 'publisher')
    list_filter = ('format', 'genre', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 25
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('title', 'author', 'description', 'genre'),
            'classes': ('wide',)
        }),
        ('Szczegóły książki', {
            'fields': ('isbn', 'publisher', 'publication_year', 'page_count'),
        }),
        ('Format i dostępność', {
            'fields': ('format', 'price', 'stock'),
        }),
        ('Wydawca/Sprzedawca', {
            'fields': ('vendor_company',),
        }),
        ('Multimedia', {
            'fields': ('image_url',),
        }),
    )
    
    readonly_fields = ('created_at',)
