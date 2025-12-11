"""
Przykłady zaawansowanej customizacji Django Admin
Umieść ten kod w odpowiednich plikach admin.py
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum


# ============================================
# PRZYKŁAD 1: Kolorowe statusy w liście
# ============================================

@admin.register(Order)
class OrderAdminEnhanced(admin.ModelAdmin):
    list_display = ['id', 'get_customer', 'colored_status', 'total_amount', 'created_at']
    
    def colored_status(self, obj):
        """Wyświetla status z kolorowym badge'em"""
        colors = {
            'pending': '#FFA500',      # Pomarańczowy
            'processing': '#8CA9FF',    # Niebieski (z palety)
            'completed': '#28a745',     # Zielony
            'cancelled': '#dc3545',     # Czerwony
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; '
            'border-radius: 12px; font-weight: 600; font-size: 0.85rem;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    colored_status.short_description = 'Status'


# ============================================
# PRZYKŁAD 2: Thumbnail w liście produktów
# ============================================

@admin.register(Product)
class ProductAdminEnhanced(admin.ModelAdmin):
    list_display = ['thumbnail', 'title', 'author', 'colored_price', 'stock_badge', 'format']
    
    def thumbnail(self, obj):
        """Wyświetla miniaturę okładki"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 70px; '
                'object-fit: cover; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                obj.cover_image.url
            )
        return format_html(
            '<div style="width: 50px; height: 70px; background: #AAC4F5; '
            'border-radius: 6px; display: flex; align-items: center; '
            'justify-content: center; color: white; font-weight: bold;">?</div>'
        )
    thumbnail.short_description = '📷'
    
    def colored_price(self, obj):
        """Wyświetla cenę z formatowaniem"""
        return format_html(
            '<span style="color: #8CA9FF; font-weight: 600; font-size: 1.1rem;">{} zł</span>',
            obj.price
        )
    colored_price.short_description = 'Cena'
    
    def stock_badge(self, obj):
        """Wyświetla stan magazynowy z kolorowym badge'em"""
        if obj.stock == 0:
            color = '#dc3545'
            text = 'Wyprzedane'
        elif obj.stock < 10:
            color = '#ffc107'
            text = f'Niski: {obj.stock}'
        else:
            color = '#28a745'
            text = f'OK: {obj.stock}'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; '
            'border-radius: 10px; font-size: 0.8rem; font-weight: 600;">{}</span>',
            color, text
        )
    stock_badge.short_description = 'Magazyn'


# ============================================
# PRZYKŁAD 3: Dashboard z statystykami
# ============================================

class CustomAdminSite(admin.AdminSite):
    site_header = "🛍️ E-Commerce Admin Panel"
    site_title = "E-Commerce Admin"
    index_title = "Panel zarządzania sklepem"
    
    def index(self, request, extra_context=None):
        """Dodaje statystyki do dashboardu"""
        from django.db.models import Count, Sum
        from products.models import Product
        from orders.models import Order
        from users.models import CustomUser
        
        extra_context = extra_context or {}
        
        # Statystyki
        stats = {
            'total_products': Product.objects.count(),
            'low_stock_products': Product.objects.filter(stock__lt=10).count(),
            'total_orders': Order.objects.count(),
            'pending_orders': Order.objects.filter(payment_status='pending').count(),
            'total_users': CustomUser.objects.filter(role='customer').count(),
            'total_vendors': CustomUser.objects.filter(role='vendor').count(),
        }
        
        # Oblicz przychód
        revenue = Order.objects.filter(is_paid=True).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        stats['total_revenue'] = revenue
        
        extra_context['stats'] = stats
        
        return super().index(request, extra_context)


# ============================================
# PRZYKŁAD 4: Custom akcje (batch actions)
# ============================================

@admin.action(description='✅ Oznacz jako dostępne (stock=100)')
def mark_as_available(modeladmin, request, queryset):
    updated = queryset.update(stock=100)
    modeladmin.message_user(
        request,
        f'Zaktualizowano {updated} produktów.',
        level='success'
    )


@admin.action(description='❌ Oznacz jako wyprzedane')
def mark_as_sold_out(modeladmin, request, queryset):
    updated = queryset.update(stock=0)
    modeladmin.message_user(
        request,
        f'Oznaczono {updated} produktów jako wyprzedane.',
        level='warning'
    )


@admin.action(description='📦 Ustaw niski stan (stock=5)')
def set_low_stock(modeladmin, request, queryset):
    updated = queryset.update(stock=5)
    modeladmin.message_user(
        request,
        f'Ustawiono niski stan dla {updated} produktów.',
        level='info'
    )


class ProductAdminWithActions(admin.ModelAdmin):
    actions = [mark_as_available, mark_as_sold_out, set_low_stock]
    list_display = ['title', 'stock', 'price']


# ============================================
# PRZYKŁAD 5: Custom filtry
# ============================================

from django.contrib.admin import SimpleListFilter

class StockLevelFilter(SimpleListFilter):
    title = 'Stan magazynowy'
    parameter_name = 'stock_level'
    
    def lookups(self, request, model_admin):
        return (
            ('high', '✅ Wysoki (>50)'),
            ('medium', '📦 Średni (10-50)'),
            ('low', '⚠️ Niski (1-10)'),
            ('out', '❌ Wyprzedane (0)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(stock__gt=50)
        if self.value() == 'medium':
            return queryset.filter(stock__gte=10, stock__lte=50)
        if self.value() == 'low':
            return queryset.filter(stock__gt=0, stock__lt=10)
        if self.value() == 'out':
            return queryset.filter(stock=0)


class PriceRangeFilter(SimpleListFilter):
    title = 'Przedział cenowy'
    parameter_name = 'price_range'
    
    def lookups(self, request, model_admin):
        return (
            ('budget', '💰 Budget (<30 zł)'),
            ('mid', '💵 Średnia (30-60 zł)'),
            ('premium', '💎 Premium (>60 zł)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'budget':
            return queryset.filter(price__lt=30)
        if self.value() == 'mid':
            return queryset.filter(price__gte=30, price__lte=60)
        if self.value() == 'premium':
            return queryset.filter(price__gt=60)


class ProductAdminWithFilters(admin.ModelAdmin):
    list_filter = [StockLevelFilter, PriceRangeFilter, 'format', 'genre']


# ============================================
# PRZYKŁAD 6: Inline z custom display
# ============================================

class OrderItemInlineEnhanced(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_thumbnail', 'subtotal', 'added_at']
    fields = ['product_thumbnail', 'product', 'quantity', 'price', 'subtotal']
    
    def product_thumbnail(self, obj):
        if obj.product and obj.product.cover_image:
            return format_html(
                '<img src="{}" style="width: 40px; height: 55px; '
                'object-fit: cover; border-radius: 4px;" />',
                obj.product.cover_image.url
            )
        return '—'
    product_thumbnail.short_description = '📷'


# ============================================
# PRZYKŁAD 7: Read-only summary fields
# ============================================

class OrderAdminWithSummary(admin.ModelAdmin):
    readonly_fields = ['order_summary', 'created_at', 'updated_at']
    
    def order_summary(self, obj):
        """Wyświetla podsumowanie zamówienia"""
        items = obj.items.all()
        items_count = items.count()
        
        html = f'''
        <div style="background: #FFF8DE; padding: 15px; border-radius: 8px; 
                    border-left: 4px solid #8CA9FF;">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">📦 Podsumowanie zamówienia</h3>
            <p><strong>Liczba pozycji:</strong> {items_count}</p>
            <p><strong>Wartość całkowita:</strong> {obj.total_amount} zł</p>
            <p><strong>Status płatności:</strong> {obj.get_payment_status_display()}</p>
            <p><strong>Klient:</strong> {obj.user.email if obj.user else 'Gość'}</p>
        </div>
        '''
        return format_html(html)
    order_summary.short_description = 'Podsumowanie'


# ============================================
# PRZYKŁAD 8: Linki do powiązanych obiektów
# ============================================

class OrderAdminWithLinks(admin.ModelAdmin):
    list_display = ['id', 'customer_link', 'items_count', 'payment_link', 'created_at']
    
    def customer_link(self, obj):
        """Link do profilu klienta"""
        if obj.user:
            url = reverse('admin:users_customuser_change', args=[obj.user.pk])
            return format_html(
                '<a href="{}" style="color: #8CA9FF; font-weight: 600;">{}</a>',
                url, obj.user.email
            )
        return 'Gość'
    customer_link.short_description = 'Klient'
    
    def items_count(self, obj):
        """Liczba pozycji z linkiem"""
        count = obj.items.count()
        return format_html(
            '<span style="background: #AAC4F5; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 0.85rem;">{} szt.</span>',
            count
        )
    items_count.short_description = 'Pozycje'
    
    def payment_link(self, obj):
        """Link do płatności"""
        try:
            payment = obj.payment
            url = reverse('admin:payments_payment_change', args=[payment.pk])
            status_colors = {
                'pending': '#FFA500',
                'succeeded': '#28a745',
                'failed': '#dc3545',
            }
            color = status_colors.get(payment.status, '#6c757d')
            return format_html(
                '<a href="{}" style="background: {}; color: white; padding: 4px 10px; '
                'border-radius: 8px; text-decoration: none; font-size: 0.85rem;">{}</a>',
                url, color, payment.get_status_display()
            )
        except:
            return '—'
    payment_link.short_description = 'Płatność'


# ============================================
# PRZYKŁAD 9: Grupowanie fieldsets z ikonami
# ============================================

class ProductAdminGrouped(admin.ModelAdmin):
    fieldsets = (
        ('📚 Podstawowe informacje', {
            'fields': ('title', 'author', 'description', 'genre'),
            'classes': ('wide',),
            'description': 'Główne informacje o książce'
        }),
        ('📖 Szczegóły publikacji', {
            'fields': ('isbn', 'publisher', 'publication_year', 'language', 'page_count'),
            'classes': ('collapse',),
        }),
        ('💰 Cena i format', {
            'fields': ('format', 'price', 'stock'),
            'classes': ('wide',),
        }),
        ('🏢 Sprzedawca', {
            'fields': ('vendor',),
            'classes': ('collapse',),
        }),
        ('🖼️ Media', {
            'fields': ('cover_image',),
        }),
        ('📅 Daty systemowe', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ============================================
# PRZYKŁAD 10: Custom admin site (zamień domyślny)
# ============================================

# W backend/admin.py lub jako oddzielny plik:

from django.contrib import admin

class ECommerceAdminSite(admin.AdminSite):
    site_header = "🛍️ E-Commerce Admin Panel"
    site_title = "E-Commerce"
    index_title = "Witaj w panelu administracyjnym"
    
    def each_context(self, request):
        """Dodaje custom context do każdej strony admina"""
        context = super().each_context(request)
        context['custom_greeting'] = f"Witaj, {request.user.first_name or request.user.username}!"
        return context


# Użycie:
# admin_site = ECommerceAdminSite(name='ecommerce_admin')
# 
# W urls.py:
# from backend.admin import admin_site
# urlpatterns = [
#     path('admin/', admin_site.urls),
#     ...
# ]


# ============================================
# INSTRUKCJE UŻYCIA
# ============================================

"""
1. Skopiuj wybrane przykłady do odpowiednich plików admin.py
2. Dostosuj nazwy modeli do swoich potrzeb
3. Uruchom serwer i przetestuj
4. Kombinuj różne techniki dla najlepszego efektu

WSKAZÓWKI:
- Użyj format_html() dla bezpiecznego HTML
- Dodaj emoji dla lepszej czytelności
- Używaj kolorów z palety projektu (#8CA9FF, #AAC4F5, #FFF8DE, #FFF2C6)
- Grupuj powiązane informacje w fieldsets
- Dodawaj readonly_fields dla lepszego UX
- Wykorzystuj inline dla relacji
"""
