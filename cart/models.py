from django.db import models
from django.conf import settings
from products.models import Product
import uuid


class Cart(models.Model):
    """
    Model representing a shopping cart for a user.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'koszyk'
        verbose_name_plural = 'koszyki'
    
    def __str__(self):
        return f"Cart for {self.user.email}"
    
    @property
    def total_price(self):
        """Calculate total price of all items in the cart."""
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def total_items(self):
        """Calculate total number of items in the cart."""
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """
    Model representing an item in a shopping cart.
    """
    FORMAT_CHOICES = [
        ('paperback', 'Książka papierowa'),
        ('ebook', 'E-book'),
    ]
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    selected_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'pozycja koszyka'
        verbose_name_plural = 'pozycje koszyka'
        unique_together = ('cart', 'product', 'selected_format')
    
    def __str__(self):
        format_str = f" ({self.get_selected_format_display()})" if self.selected_format else ""
        return f"{self.quantity}x {self.product.title}{format_str} in {self.cart.user.email}'s cart"
    
    @property
    def subtotal(self):
        """Calculate subtotal for this cart item."""
        return self.quantity * self.product.price


class GuestCart(models.Model):
    """
    Model representing a shopping cart for a guest (unauthenticated) user.
    Uses session_key to track the cart.
    """
    session_key = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'koszyk gościa'
        verbose_name_plural = 'koszyki gości'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Guest Cart {self.session_key[:8]}..."
    
    @property
    def total_price(self):
        """Calculate total price of all items in the cart."""
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def total_items(self):
        """Calculate total number of items in the cart."""
        return sum(item.quantity for item in self.items.all())


class GuestCartItem(models.Model):
    """
    Model representing an item in a guest shopping cart.
    """
    FORMAT_CHOICES = [
        ('paperback', 'Książka papierowa'),
        ('ebook', 'E-book'),
    ]
    
    cart = models.ForeignKey(GuestCart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='guest_cart_items')
    quantity = models.PositiveIntegerField(default=1)
    selected_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'pozycja koszyka gościa'
        verbose_name_plural = 'pozycje koszyka gościa'
        unique_together = ('cart', 'product', 'selected_format')
    
    def __str__(self):
        format_str = f" ({self.get_selected_format_display()})" if self.selected_format else ""
        return f"{self.quantity}x {self.product.title}{format_str} in Guest Cart"
    
    @property
    def subtotal(self):
        """Calculate subtotal for this cart item."""
        return self.quantity * self.product.price
