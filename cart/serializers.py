from rest_framework import serializers
from .models import Cart, CartItem, GuestCart, GuestCartItem
from products.serializers import ProductSerializer
import re


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the CartItem model.
    """
    product_details = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_details', 'quantity', 'selected_format', 'subtotal', 'added_at']
        read_only_fields = ['id', 'added_at']
    
    def validate_quantity(self, value):
        """
        Validate that quantity is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
    
    def validate(self, attrs):
        """
        Validate that product has sufficient stock and format is valid.
        """
        product = attrs.get('product')
        quantity = attrs.get('quantity')
        selected_format = attrs.get('selected_format')
        
        if product:
            # Validate format selection for products with 'both' format
            if product.format == 'both':
                if not selected_format:
                    raise serializers.ValidationError(
                        {"selected_format": "Musisz wybrać format: książka papierowa lub e-book."}
                    )
                if selected_format not in ['paperback', 'ebook']:
                    raise serializers.ValidationError(
                        {"selected_format": "Nieprawidłowy format. Wybierz 'paperback' lub 'ebook'."}
                    )
            elif product.format == 'paperback':
                if selected_format and selected_format != 'paperback':
                    raise serializers.ValidationError(
                        {"selected_format": "Ten produkt dostępny jest tylko jako książka papierowa."}
                    )
                attrs['selected_format'] = 'paperback'
            elif product.format == 'ebook':
                if selected_format and selected_format != 'ebook':
                    raise serializers.ValidationError(
                        {"selected_format": "Ten produkt dostępny jest tylko jako e-book."}
                    )
                attrs['selected_format'] = 'ebook'
            
            # Validate stock
            if quantity and quantity > product.stock:
                raise serializers.ValidationError(
                    {"quantity": f"Dostępnych tylko {product.stock} sztuk."}
                )
        
        return attrs


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for the Cart model.
    """
    items = CartItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    total_price = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'user_email', 'created_at', 'updated_at', 'items', 'total_price', 'total_items']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    """
    Serializer for adding items to cart.
    """
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)
    selected_format = serializers.ChoiceField(choices=['paperback', 'ebook'], required=False, allow_null=True)
    
    def validate_quantity(self, value):
        """
        Validate that quantity is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class GuestCartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the GuestCartItem model.
    """
    product_details = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = GuestCartItem
        fields = ['id', 'product', 'product_details', 'quantity', 'selected_format', 'subtotal', 'added_at']
        read_only_fields = ['id', 'added_at']
    
    def validate_quantity(self, value):
        """
        Validate that quantity is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Ilość musi być większa od zera.")
        return value
    
    def validate(self, attrs):
        """
        Validate that product has sufficient stock and format is valid.
        """
        product = attrs.get('product')
        quantity = attrs.get('quantity')
        selected_format = attrs.get('selected_format')
        
        if product:
            # Validate format selection for products with 'both' format
            if product.format == 'both':
                if not selected_format:
                    raise serializers.ValidationError(
                        {"selected_format": "Musisz wybrać format: książka papierowa lub e-book."}
                    )
                if selected_format not in ['paperback', 'ebook']:
                    raise serializers.ValidationError(
                        {"selected_format": "Nieprawidłowy format. Wybierz 'paperback' lub 'ebook'."}
                    )
            elif product.format == 'paperback':
                if selected_format and selected_format != 'paperback':
                    raise serializers.ValidationError(
                        {"selected_format": "Ten produkt dostępny jest tylko jako książka papierowa."}
                    )
                attrs['selected_format'] = 'paperback'
            elif product.format == 'ebook':
                if selected_format and selected_format != 'ebook':
                    raise serializers.ValidationError(
                        {"selected_format": "Ten produkt dostępny jest tylko jako e-book."}
                    )
                attrs['selected_format'] = 'ebook'
            
            # Validate stock
            if quantity and quantity > product.stock:
                raise serializers.ValidationError(
                    {"quantity": f"Dostępnych tylko {product.stock} sztuk."}
                )
        
        return attrs


class GuestCartSerializer(serializers.ModelSerializer):
    """
    Serializer for the GuestCart model.
    """
    items = GuestCartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()
    
    class Meta:
        model = GuestCart
        fields = ['id', 'session_key', 'created_at', 'updated_at', 'items', 'total_price', 'total_items']
        read_only_fields = ['id', 'session_key', 'created_at', 'updated_at']


class AddToGuestCartSerializer(serializers.Serializer):
    """
    Serializer for adding items to guest cart.
    """
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)
    selected_format = serializers.ChoiceField(choices=['paperback', 'ebook'], required=False, allow_null=True)
    
    def validate_quantity(self, value):
        """
        Validate that quantity is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Ilość musi być większa od zera.")
        return value
