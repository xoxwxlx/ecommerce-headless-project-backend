from django.db import models
from django.conf import settings
from orders.models import Order


class Payment(models.Model):
    """
    Model representing a payment transaction.
    """
    STATUS_CHOICES = [
        ('pending', 'Oczekująca'),
        ('completed', 'Zakończona'),
        ('failed', 'Nieudana'),
        ('refunded', 'Zwrócona'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    stripe_session_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'płatność'
        verbose_name_plural = 'płatności'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.status}"
