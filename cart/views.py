from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import DestroyAPIView
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from products.models import Product
from .serializers import CartSerializer, AddToCartSerializer, CartItemSerializer


class AddToCartView(APIView):
    """
    API endpoint to add items to cart.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        selected_format = serializer.validated_data.get('selected_format')
        
        # Get or create cart for user
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Get product
        product = get_object_or_404(Product, id=product_id)
        
        # Validate format selection
        if product.format == 'both':
            if not selected_format:
                return Response(
                    {'error': 'Musisz wybrać format: paperback (książka papierowa) lub ebook (e-book).'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif product.format == 'paperback':
            selected_format = 'paperback'
        elif product.format == 'ebook':
            selected_format = 'ebook'
        
        # Check stock availability
        if quantity > product.stock:
            return Response(
                {'error': f'Dostępnych tylko {product.stock} sztuk.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            selected_format=selected_format,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return Response(
                    {'error': f'Nie można dodać {quantity} więcej. Dostępnych tylko {product.stock - cart_item.quantity} sztuk.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity = new_quantity
            cart_item.save()
        
        return Response(
            CartItemSerializer(cart_item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class CartView(APIView):
    """
    API endpoint to retrieve user's cart.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RemoveFromCartView(DestroyAPIView):
    """
    API endpoint to remove an item from cart.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartItemSerializer
    
    def get_queryset(self):
        # Only allow users to delete items from their own cart
        return CartItem.objects.filter(cart__user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Item removed from cart successfully.'},
            status=status.HTTP_200_OK
        )
