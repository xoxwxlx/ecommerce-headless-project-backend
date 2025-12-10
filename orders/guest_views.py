from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from .models import Order, OrderItem, GuestOrderAddress
from .serializers import GuestCheckoutSerializer, GuestOrderSerializer
from cart.models import GuestCart, GuestCartItem


class GuestCheckoutView(APIView):
    """
    API endpoint for guest checkout.
    POST /api/checkout/guest
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Validate request data
        serializer = GuestCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get guest cart
        session_key = request.session.session_key
        
        if not session_key:
            return Response(
                {'error': 'Nie znaleziono koszyka. Dodaj produkty do koszyka przed zakupem.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            guest_cart = GuestCart.objects.get(session_key=session_key)
        except GuestCart.DoesNotExist:
            return Response(
                {'error': 'Nie znaleziono koszyka. Dodaj produkty do koszyka przed zakupem.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if cart is empty
        if not guest_cart.items.exists():
            return Response(
                {'error': 'Koszyk jest pusty. Dodaj produkty przed zakupem.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate stock for all items
        for item in guest_cart.items.all():
            if item.quantity > item.product.stock:
                return Response(
                    {'error': f'Produkt "{item.product.title}" nie ma wystarczającej ilości w magazynie. Dostępne: {item.product.stock}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create order and order items in transaction
        try:
            with transaction.atomic():
                # Create guest order
                order = Order.objects.create(
                    order_type='guest',
                    user=None,
                    guest_email=serializer.validated_data['email'],
                    guest_first_name=serializer.validated_data['first_name'],
                    guest_last_name=serializer.validated_data['last_name'],
                    guest_phone=serializer.validated_data['phone'],
                    total_amount=guest_cart.total_price,
                    payment_status='pending'
                )
                
                # Create delivery address
                address_data = serializer.validated_data['address']
                GuestOrderAddress.objects.create(
                    order=order,
                    **address_data
                )
                
                # Create order items and update stock
                for cart_item in guest_cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price,
                        selected_format=cart_item.selected_format
                    )
                    
                    # Update product stock
                    cart_item.product.stock -= cart_item.quantity
                    cart_item.product.save()
                
                # Clear guest cart
                guest_cart.items.all().delete()
                
                # Send confirmation email
                try:
                    self.send_order_confirmation_email(order)
                except Exception as e:
                    # Log error but don't fail the order
                    print(f"Error sending email: {e}")
                
                # Return order details
                order_serializer = GuestOrderSerializer(order)
                return Response({
                    'message': 'Zamówienie zostało złożone pomyślnie',
                    'order': order_serializer.data,
                    'payment_required': True,
                    'order_id': order.id
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': f'Błąd podczas tworzenia zamówienia: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def send_order_confirmation_email(self, order):
        """
        Send order confirmation email to guest customer.
        """
        subject = f'Potwierdzenie zamówienia #{order.id}'
        
        # Format items list
        items_list = []
        for item in order.items.all():
            format_str = f" ({item.get_selected_format_display()})" if item.selected_format else ""
            items_list.append(
                f"- {item.product.title}{format_str} x {item.quantity} - {item.subtotal} PLN"
            )
        items_text = "\n".join(items_list)
        
        # Get delivery address
        address = order.guest_address
        
        message = f"""
Dziękujemy za złożenie zamówienia!

Szczegóły zamówienia:
Numer zamówienia: #{order.id}
Data: {order.created_at.strftime('%d.%m.%Y %H:%M')}

Dane zamawiającego:
Imię i nazwisko: {order.guest_first_name} {order.guest_last_name}
Email: {order.guest_email}
Telefon: {order.guest_phone}

Adres dostawy:
{address.recipient_name}
{address.street}
{address.postal_code} {address.city}
{address.country}
Tel: {address.phone}

Zamówione produkty:
{items_text}

Łącznie: {order.total_amount} PLN

Status płatności: {order.get_payment_status_display()}

Aby dokończyć zamówienie, prosimy o dokonanie płatności.

Pozdrawiamy,
Zespół Księgarni
"""
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.guest_email],
            fail_silently=False,
        )
