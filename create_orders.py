import os
import django
import random
from decimal import Decimal
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from products.models import Product
from orders.models import Order, OrderItem, GuestOrderAddress
from users.models import Address

User = get_user_model()

def create_sample_orders():
    """Create 50 sample orders with realistic data"""
    
    # Get all products
    products = list(Product.objects.all())
    if not products:
        print("Brak produktów w bazie. Najpierw dodaj produkty.")
        return
    
    # Get all users (customers)
    customers = list(User.objects.filter(role='customer'))
    if not customers:
        print("Brak klientów w bazie. Tworzę przykładowych klientów...")
        # Create sample customers
        for i in range(10):
            user = User.objects.create_user(
                email=f'customer{i+1}@example.com',
                password='testpass123',
                role='customer',
                first_name=random.choice(['Jan', 'Anna', 'Piotr', 'Maria', 'Tomasz', 'Katarzyna', 'Michał', 'Agnieszka']),
                last_name=random.choice(['Kowalski', 'Nowak', 'Wiśniewski', 'Wójcik', 'Kowalczyk', 'Kamiński', 'Lewandowski'])
            )
            customers.append(user)
            
            # Create address for each customer
            Address.objects.create(
                user=user,
                recipient_name=f"{user.first_name} {user.last_name}",
                street=f"ul. {random.choice(['Główna', 'Kwiatowa', 'Słoneczna', 'Piękna', 'Długa'])} {random.randint(1, 100)}",
                city=random.choice(['Warszawa', 'Kraków', 'Wrocław', 'Poznań', 'Gdańsk', 'Szczecin', 'Lublin']),
                postal_code=f"{random.randint(10, 99)}-{random.randint(100, 999)}",
                country='Polska',
                phone=f"+48{random.randint(500000000, 799999999)}",
                is_default=True
            )
        print(f"Utworzono {len(customers)} przykładowych klientów.")
    
    # Payment statuses available in model
    payment_statuses = ['pending', 'paid', 'failed']
    formats = ['paperback', 'ebook']  # Only formats available in OrderItem model
    
    orders_created = 0
    
    for i in range(50):
        # Select random customer
        customer = random.choice(customers)
        address = Address.objects.filter(user=customer, is_default=True).first()
        
        if not address:
            continue
        
        # Random date within last 60 days
        days_ago = random.randint(0, 60)
        order_date = timezone.now() - timedelta(days=days_ago)
        
        # Payment status
        payment_status = random.choice(payment_statuses)
        
        # Calculate total before creating order
        num_items = random.randint(1, 5)
        selected_products = random.sample(products, min(num_items, len(products)))
        
        total_amount = Decimal('0.00')
        for product in selected_products:
            quantity = random.randint(1, 3)
            total_amount += product.price * quantity
        
        # Create order
        order = Order.objects.create(
            user=customer,
            order_type='user',
            payment_status=payment_status,
            total_amount=total_amount
        )
        
        # Set created_at manually
        order.created_at = order_date
        order.save()
        
        # Add order items
        for product in selected_products:
            quantity = random.randint(1, 3)
            selected_format = random.choice(formats)
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price,
                selected_format=selected_format
            )
        
        orders_created += 1
        
        # Print progress
        if orders_created % 10 == 0:
            print(f"Utworzono {orders_created} zamówień...")
    
    print(f"\n✅ Sukces! Utworzono {orders_created} zamówień.")
    print(f"Zamówienia od różnych klientów z datami z ostatnich 60 dni.")
    
    # Show statistics
    print("\n📊 Statystyki zamówień:")
    for status in ['pending', 'paid', 'failed']:
        count = Order.objects.filter(payment_status=status).count()
        print(f"  {status}: {count}")

if __name__ == '__main__':
    create_sample_orders()
