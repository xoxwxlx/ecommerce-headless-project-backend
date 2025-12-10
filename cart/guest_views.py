from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import GuestCart, GuestCartItem
from .serializers import GuestCartSerializer, GuestCartItemSerializer, AddToGuestCartSerializer
from products.models import Product
import uuid


def get_or_create_guest_session(request):
    """
    Get or create a session key for guest users.
    """
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


class GuestCartView(APIView):
    """
    API endpoint to get guest cart.
    GET /api/cart/guest
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        session_key = get_or_create_guest_session(request)
        
        # Get or create guest cart
        guest_cart, created = GuestCart.objects.get_or_create(session_key=session_key)
        
        serializer = GuestCartSerializer(guest_cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddToGuestCartView(APIView):
    """
    API endpoint to add items to guest cart.
    POST /api/cart/guest/add
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = AddToGuestCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_key = get_or_create_guest_session(request)
        
        # Get or create guest cart
        guest_cart, created = GuestCart.objects.get_or_create(session_key=session_key)
        
        # Get product
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        selected_format = serializer.validated_data.get('selected_format')
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Produkt nie został znaleziony'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate format selection
        if product.format == 'both' and not selected_format:
            return Response(
                {'error': 'Musisz wybrać format: książka papierowa lub e-book'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set default format for single-format products
        if product.format == 'paperback':
            selected_format = 'paperback'
        elif product.format == 'ebook':
            selected_format = 'ebook'
        
        # Check stock
        if quantity > product.stock:
            return Response(
                {'error': f'Dostępnych tylko {product.stock} sztuk'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if item already exists in cart
        cart_item, created = GuestCartItem.objects.get_or_create(
            cart=guest_cart,
            product=product,
            selected_format=selected_format,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return Response(
                    {'error': f'Dostępnych tylko {product.stock} sztuk. W koszyku masz już {cart_item.quantity}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity = new_quantity
            cart_item.save()
        
        # Return updated cart
        cart_serializer = GuestCartSerializer(guest_cart)
        return Response({
            'message': 'Produkt dodany do koszyka',
            'cart': cart_serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class UpdateGuestCartItemView(APIView):
    """
    API endpoint to update quantity of guest cart item.
    PATCH /api/cart/guest/update/:id
    """
    permission_classes = [permissions.AllowAny]
    
    def patch(self, request, pk):
        session_key = request.session.session_key
        
        if not session_key:
            return Response(
                {'error': 'Nie znaleziono koszyka gościa'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            guest_cart = GuestCart.objects.get(session_key=session_key)
            cart_item = GuestCartItem.objects.get(pk=pk, cart=guest_cart)
        except (GuestCart.DoesNotExist, GuestCartItem.DoesNotExist):
            return Response(
                {'error': 'Produkt nie został znaleziony w koszyku'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get new quantity
        quantity = request.data.get('quantity')
        if not quantity:
            return Response(
                {'error': 'Podaj nową ilość'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {'error': 'Ilość musi być większa od zera'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {'error': 'Nieprawidłowa wartość ilości'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check stock
        if quantity > cart_item.product.stock:
            return Response(
                {'error': f'Dostępnych tylko {cart_item.product.stock} sztuk'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update quantity
        cart_item.quantity = quantity
        cart_item.save()
        
        # Return updated cart
        cart_serializer = GuestCartSerializer(guest_cart)
        return Response({
            'message': 'Ilość zaktualizowana',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)


class RemoveFromGuestCartView(APIView):
    """
    API endpoint to remove item from guest cart.
    DELETE /api/cart/guest/remove/:id
    """
    permission_classes = [permissions.AllowAny]
    
    def delete(self, request, pk):
        session_key = request.session.session_key
        
        if not session_key:
            return Response(
                {'error': 'Nie znaleziono koszyka gościa'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            guest_cart = GuestCart.objects.get(session_key=session_key)
            cart_item = GuestCartItem.objects.get(pk=pk, cart=guest_cart)
        except (GuestCart.DoesNotExist, GuestCartItem.DoesNotExist):
            return Response(
                {'error': 'Produkt nie został znaleziony w koszyku'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        cart_item.delete()
        
        # Return updated cart
        cart_serializer = GuestCartSerializer(guest_cart)
        return Response({
            'message': 'Produkt usunięty z koszyka',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)


class ClearGuestCartView(APIView):
    """
    API endpoint to clear guest cart.
    DELETE /api/cart/guest/clear
    """
    permission_classes = [permissions.AllowAny]
    
    def delete(self, request):
        session_key = request.session.session_key
        
        if not session_key:
            return Response(
                {'message': 'Koszyk jest już pusty'},
                status=status.HTTP_200_OK
            )
        
        try:
            guest_cart = GuestCart.objects.get(session_key=session_key)
            guest_cart.items.all().delete()
            
            cart_serializer = GuestCartSerializer(guest_cart)
            return Response({
                'message': 'Koszyk został wyczyszczony',
                'cart': cart_serializer.data
            }, status=status.HTTP_200_OK)
        except GuestCart.DoesNotExist:
            return Response(
                {'message': 'Koszyk jest już pusty'},
                status=status.HTTP_200_OK
            )
