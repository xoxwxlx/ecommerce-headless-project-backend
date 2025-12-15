from rest_framework import serializers
from .models import Order, OrderItem, GuestOrderAddress
from products.serializers import ProductSerializer
import re


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the OrderItem model.
    """
    product_details = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_details', 'quantity', 'price', 'selected_format', 'subtotal']
        read_only_fields = ['id']
    
    def validate_quantity(self, value):
        """
        Validate that quantity is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for the Order model.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_paid = serializers.ReadOnlyField()
    user_address = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'user_email', 'user_address', 'total_amount', 'payment_status', 'created_at', 'updated_at', 'items', 'is_paid']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_total_amount(self, value):
        """
        Validate that total_amount is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Total amount must be greater than zero.")
        return value


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating orders with items.
    """
    items = OrderItemSerializer(many=True)
    user_address_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Order
        fields = ['user', 'user_address_id', 'total_amount', 'payment_status', 'items']

    def create(self, validated_data):
        """
        Create order with items and user address if provided.
        """
        items_data = validated_data.pop('items')
        user_address_id = validated_data.pop('user_address_id', None)
        order = Order.objects.create(**validated_data)
        if user_address_id:
            from users.models import Address
            try:
                address = Address.objects.get(id=user_address_id, user=order.user)
                order.user_address = address
                order.save()
            except Address.DoesNotExist:
                pass
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order


class GuestOrderAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for guest order delivery address.
    """
    class Meta:
        model = GuestOrderAddress
        fields = ['recipient_name', 'street', 'postal_code', 'city', 'country', 'phone']
    
    def validate_recipient_name(self, value):
        """Validate recipient name is not empty."""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Imię i nazwisko odbiorcy musi zawierać co najmniej 2 znaki")
        return value.strip()
    
    def validate_postal_code(self, value):
        """Validate Polish postal code format (XX-XXX)."""
        if value:
            cleaned = value.replace(' ', '').replace('-', '')
            if not re.match(r'^\d{5}$', cleaned):
                raise serializers.ValidationError("Kod pocztowy musi być w formacie XX-XXX (np. 00-950)")
            if '-' not in value:
                value = f"{cleaned[:2]}-{cleaned[2:]}"
        return value
    
    def validate_phone(self, value):
        """Validate phone number format."""
        if value:
            cleaned = value.replace(' ', '').replace('-', '').replace('+', '')
            if not re.match(r'^[\d\+\s\-]+$', value):
                raise serializers.ValidationError("Numer telefonu może zawierać tylko cyfry, spacje, myślniki i znak +")
            if len(cleaned) < 9 or len(cleaned) > 15:
                raise serializers.ValidationError("Numer telefonu musi zawierać od 9 do 15 cyfr")
        return value
    
    def validate_street(self, value):
        """Validate street address is not empty."""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Ulica i numer muszą zawierać co najmniej 3 znaki")
        return value.strip()
    
    def validate_city(self, value):
        """Validate city name is not empty."""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Nazwa miasta musi zawierać co najmniej 2 znaki")
        return value.strip()


class GuestCheckoutSerializer(serializers.Serializer):
    """
    Serializer for guest checkout process.
    """
    # Personal info
    first_name = serializers.CharField(required=True, max_length=100)
    last_name = serializers.CharField(required=True, max_length=100)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True, max_length=20)
    
    # Delivery address
    address = GuestOrderAddressSerializer(required=True)
    
    def validate_first_name(self, value):
        """Validate first name is not empty."""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Imię musi zawierać co najmniej 2 znaki")
        return value.strip()
    
    def validate_last_name(self, value):
        """Validate last name is not empty."""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Nazwisko musi zawierać co najmniej 2 znaki")
        return value.strip()
    
    def validate_phone(self, value):
        """Validate phone number format."""
        if value:
            cleaned = value.replace(' ', '').replace('-', '').replace('+', '')
            if not re.match(r'^[\d\+\s\-]+$', value):
                raise serializers.ValidationError("Numer telefonu może zawierać tylko cyfry, spacje, myślniki i znak +")
            if len(cleaned) < 9 or len(cleaned) > 15:
                raise serializers.ValidationError("Numer telefonu musi zawierać od 9 do 15 cyfr")
        return value


class GuestOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for guest orders with address info.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    guest_address = GuestOrderAddressSerializer(read_only=True)
    is_paid = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = ['id', 'order_type', 'guest_email', 'guest_first_name', 'guest_last_name', 
                  'guest_phone', 'total_amount', 'payment_status', 'created_at', 'updated_at', 
                  'items', 'guest_address', 'is_paid']
        read_only_fields = ['id', 'order_type', 'created_at', 'updated_at']
