from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model.
    """
    is_in_stock = serializers.ReadOnlyField()
    vendor_company_name = serializers.CharField(source='vendor_company.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'vendor_company', 'vendor_company_name', 'title', 'author', 'genre', 'format', 'description', 'price', 'stock', 'image_url', 'publication_year', 'publisher', 'isbn', 'page_count', 'created_at', 'is_in_stock']
        read_only_fields = ['id', 'vendor_company', 'created_at']
    
    def validate_price(self, value):
        """
        Validate that price is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value
    
    def validate_stock(self, value):
        """
        Validate that stock is not negative.
        """
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value
