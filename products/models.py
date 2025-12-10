from django.db import models
from django.conf import settings
from users.models import VendorCompany


class Product(models.Model):
    """
    Model representing a product in the e-commerce system.
    """
    GENRE_CHOICES = [
        ('romance', 'Romans'),
        ('mystery', 'Kryminał'),
        ('thriller', 'Thriller'),
        ('fantasy', 'Fantasy'),
        ('science-fiction', 'Science Fiction'),
        ('young-adult', 'Literatura młodzieżowa'),
        ('horror', 'Horror'),
    ]
    
    FORMAT_CHOICES = [
        ('paperback', 'Książka papierowa'),
        ('ebook', 'E-book'),
        ('both', 'Książka papierowa i E-book'),
    ]
    
    vendor_company = models.ForeignKey(VendorCompany, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES, default='fantasy')
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='paperback')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    publication_year = models.IntegerField(null=True, blank=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    isbn = models.CharField(max_length=13, unique=True, null=True, blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'produkt'
        verbose_name_plural = 'produkty'
        indexes = [
            models.Index(fields=['genre']),
            models.Index(fields=['format']),
            models.Index(fields=['isbn']),
            models.Index(fields=['vendor_company']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_in_stock(self):
        """Check if product is available in stock."""
        return self.stock > 0
