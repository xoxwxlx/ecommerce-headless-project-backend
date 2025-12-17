from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import stripe

from cart.models import Cart
from orders.models import Order, OrderItem
from .models import Payment
from django.db import transaction

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    """
    Endpoint API do tworzenia sesji Stripe checkout z koszyka użytkownika.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        # Pobierz koszyk użytkownika
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {'error': 'Cart is empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sprawdź, czy koszyk zawiera produkty
        cart_items = cart.items.all()
        if not cart_items.exists():
            return Response(
                {'error': 'Cart is empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sprawdź dostępność produktów w magazynie
        for cart_item in cart_items:
            if cart_item.quantity > cart_item.product.stock:
                return Response(
                    {'error': f'Insufficient stock for {cart_item.product.title}. Only {cart_item.product.stock} available.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Oblicz łączną kwotę
        total_amount = cart.total_price
        
        # Utwórz zamówienie
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            payment_status='pending'
        )
        
        # Utwórz pozycje zamówienia i zaktualizuj stan magazynowy produktu
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                selected_format=cart_item.selected_format
            )
            
            # Aktualizuj stan magazynowy produktu
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()
        
        # Zbuduj pozycje dla Stripe
        line_items = []
        for cart_item in cart_items:
            format_str = f" - {cart_item.get_selected_format_display()}" if cart_item.selected_format else ""
            line_items.append({
                'price_data': {
                    'currency': 'pln',
                    'product_data': {
                        'name': f"{cart_item.product.title}{format_str}",
                        'description': cart_item.product.author,
                    },
                    'unit_amount': int(cart_item.product.price * 100),  # Przelicz na grosze
                },
                'quantity': cart_item.quantity,
            })
        
        try:
            # Utwórz sesję Stripe checkout
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/payment/cancel",
                metadata={
                    'order_id': order.id,
                    'user_id': request.user.id,
                }
            )
            
            # Utwórz rekord płatności
            Payment.objects.create(
                order=order,
                stripe_session_id=checkout_session.id,
                amount=total_amount,
                status='pending'
            )
            
            # Wyczyść koszyk
            cart_items.delete()
            
            return Response(
                {'url': checkout_session.url},
                status=status.HTTP_200_OK
            )
            
        except stripe.error.StripeError as e:
            # Wycofaj zamówienie, jeśli utworzenie sesji Stripe się nie powiedzie
            order.delete()
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Endpoint API do obsługi zdarzeń webhook Stripe.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            return Response(
                {'error': 'Missing Stripe signature header.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Weryfikuj podpis webhooka
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            # Nieprawidłowy payload
            return Response(
                {'error': 'Invalid payload.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except stripe.error.SignatureVerificationError:
            # Nieprawidłowy podpis
            return Response(
                {'error': 'Invalid signature.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obsłuż zdarzenie checkout.session.completed
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            try:
                # Pobierz płatność po session_id
                payment = Payment.objects.get(stripe_session_id=session['id'])
                
                # Zaktualizuj status płatności
                payment.status = 'completed'
                payment.save()
                
                # Zaktualizuj status płatności zamówienia
                order = payment.order
                order.payment_status = 'paid'
                order.save()
                
                # Wyślij e-mail z potwierdzeniem
                self.send_order_confirmation_email(order)
                
            except Payment.DoesNotExist:
                return Response(
                    {'error': 'Payment not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    
    def send_order_confirmation_email(self, order):
        """
        Wyślij e-mail z potwierdzeniem zamówienia do klienta.
        """
        subject = f'Potwierdzenie zamówienia - Zamówienie #{order.id}'
        
        # Zbuduj listę pozycji zamówienia
        items_list = '\n'.join([
            f"- {item.product.title} x {item.quantity} = {item.subtotal} zł"
            for item in order.items.all()
        ])
        
        message = f"""
Szanowny Kliencie {order.user.email},

Dziękujemy za złożenie zamówienia!

Szczegóły zamówienia:
Numer zamówienia: #{order.id}
Łączna kwota: {order.total_amount} zł
Status płatności: {order.get_payment_status_display()}

Produkty:
{items_list}

Twoje zamówienie zostanie wkrótce przetworzone.

Pozdrawiamy,
Zespół E-commerce
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Zaloguj błąd, ale nie przerywaj obsługi webhooka
            print(f"Nie udało się wysłać emaila: {str(e)}")
