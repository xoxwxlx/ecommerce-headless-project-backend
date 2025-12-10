from django.db import models
from django.conf import settings
from products.models import Product


class Order(models.Model):
    """
    Model representing a customer order.
    """
    ORDER_TYPE_CHOICES = [
        ('user', 'Użytkownik'),
        ('guest', 'Gość'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Oczekująca'),
        ('paid', 'Opłacona'),
        ('failed', 'Nieudana'),
        ('refunded', 'Zwrócona'),
    ]
    
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='user')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    
    # Guest order fields
    guest_email = models.EmailField(blank=True, null=True)
    guest_first_name = models.CharField(max_length=100, blank=True, null=True)
    guest_last_name = models.CharField(max_length=100, blank=True, null=True)
    guest_phone = models.CharField(max_length=20, blank=True, null=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'zamówienie'
        verbose_name_plural = 'zamówienia'
    
    def __str__(self):
        if self.order_type == 'guest':
            return f"Order #{self.id} - {self.guest_email} (Gość)"
        return f"Order #{self.id} - {self.user.email}"
    
    @property
    def is_paid(self):
        """Check if order is paid."""
        return self.payment_status == 'paid'


class GuestOrderAddress(models.Model):
    """
    Model representing delivery address for guest orders.
    """
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='guest_address')
    recipient_name = models.CharField(max_length=200, verbose_name='Imię i nazwisko odbiorcy')
    street = models.CharField(max_length=255, verbose_name='Ulica i numer')
    postal_code = models.CharField(max_length=20, verbose_name='Kod pocztowy')
    city = models.CharField(max_length=100, verbose_name='Miasto')
    country = models.CharField(max_length=100, default='Polska', verbose_name='Kraj')
    phone = models.CharField(max_length=20, verbose_name='Numer telefonu')
    
    class Meta:
        verbose_name = 'adres zamówienia gościa'
        verbose_name_plural = 'adresy zamówień gości'
    
    def __str__(self):
        return f"Address for Order #{self.order.id} - {self.city}"


class OrderItem(models.Model):
    """
    Model representing an item in an order.
    """
    FORMAT_CHOICES = [
        ('paperback', 'Książka papierowa'),
        ('ebook', 'E-book'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    selected_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, null=True, blank=True)
    
    class Meta:
        verbose_name = 'pozycja zamówienia'
        verbose_name_plural = 'pozycje zamówień'
    
    def __str__(self):
        format_str = f" ({self.get_selected_format_display()})" if self.selected_format else ""
        return f"{self.quantity}x {self.product.title}{format_str} in Order #{self.order.id}"
    
    @property
    def subtotal(self):
        """Calculate subtotal for this order item."""
        return self.quantity * self.price
