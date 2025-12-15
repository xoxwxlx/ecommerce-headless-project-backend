from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from products.models import Product
from .serializers import OrderSerializer


class CreateOrderView(APIView):
    """
    API endpoint to create an order from user's cart.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        # Get user's cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {'error': 'Cart is empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if cart has items
        cart_items = cart.items.all()
        if not cart_items.exists():
            return Response(
                {'error': 'Cart is empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate stock availability for all items
        for cart_item in cart_items:
            if cart_item.quantity > cart_item.product.stock:
                return Response(
                    {'error': f'Insufficient stock for {cart_item.product.title}. Only {cart_item.product.stock} available.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Calculate total amount
        total_amount = sum(item.subtotal for item in cart_items)
        
        # Pobierz domyślny adres użytkownika (jeśli istnieje)
        user_address = request.user.addresses.filter(is_default=True).first()

        # Create order
        order = Order.objects.create(
            user=request.user,
            user_address=user_address,
            total_amount=total_amount,
            payment_status='pending'
        )

        # Create order items and update product stock
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                selected_format=cart_item.selected_format
            )

            # Update product stock
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()

        # Clear cart
        cart_items.delete()

        # Return created order
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    """
    API endpoint to list user's orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve a single order.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
