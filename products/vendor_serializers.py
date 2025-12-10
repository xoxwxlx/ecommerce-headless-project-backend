from rest_framework import serializers
from .models import Product


class VendorProductSerializer(serializers.ModelSerializer):
    """
    Serializer for vendor product management - allows editing only specific fields.
    """
    vendor_company_name = serializers.CharField(source='vendor_company.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'vendor_company', 'vendor_company_name', 'title', 'author', 'genre', 'format',
            'description', 'price', 'stock', 'image_url', 'publication_year',
            'publisher', 'isbn', 'page_count', 'created_at'
        ]
        read_only_fields = ['id', 'vendor_company', 'title', 'author', 'price', 'created_at']
    
    def validate(self, attrs):
        """
        Ensure vendor cannot modify protected fields.
        """
        if self.instance:
            # Check if any protected field is being modified
            protected_fields = ['title', 'author', 'price']
            for field in protected_fields:
                if field in attrs and attrs[field] != getattr(self.instance, field):
                    raise serializers.ValidationError({
                        field: f"Nie możesz edytować pola '{field}'. Skontaktuj się z administratorem."
                    })
        return attrs


class VendorProductListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing vendor products.
    """
    is_in_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'author', 'genre', 'format', 'price',
            'stock', 'image_url', 'publication_year', 'is_in_stock', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
