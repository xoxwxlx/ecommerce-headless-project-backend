from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from .models import Product
from orders.models import Order, OrderItem
from .vendor_serializers import VendorProductSerializer, VendorProductListSerializer
from .permissions import IsVendor, IsVendorOwner


class VendorProductListView(generics.ListAPIView):
    """
    GET /vendor/products
    Lista produktów należących do firmy dostawcy zalogowanego użytkownika.
    """
    serializer_class = VendorProductListSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]
    
    def get_queryset(self):
        # Zwróć produkty należące do firmy vendora
        vendor_company = self.request.user.vendor_company
        if not vendor_company:
            return Product.objects.none()
        return Product.objects.filter(vendor_company=vendor_company)


class VendorProductDetailView(generics.RetrieveUpdateAPIView):
    """
    GET/PATCH /vendor/products/:id
    Pobieranie i edycja produktu należącego do firmy dostawcy.
    Można edytować tylko: description, image_url, page_count, publication_year
    """
    serializer_class = VendorProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor, IsVendorOwner]
    
    def get_queryset(self):
        # Zwróć produkty należące do firmy vendora
        vendor_company = self.request.user.vendor_company
        if not vendor_company:
            return Product.objects.none()
        return Product.objects.filter(vendor_company=vendor_company)
    
    def patch(self, request, *args, **kwargs):
        """
        Edytuj wybrane pola produktu z walidacją.
        """
        instance = self.get_object()
        
        # Dozwolone pola do edycji
        allowed_fields = {'description', 'image_url', 'page_count', 'publication_year'}
        
        # Sprawdź czy próbuje edytować niedozwolone pola
        disallowed_fields = set(request.data.keys()) - allowed_fields
        if disallowed_fields:
            return Response(
                {
                    'error': f'Nie możesz edytować następujących pól: {", ".join(disallowed_fields)}',
                    'allowed_fields': list(allowed_fields)
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Filtruj dane tylko do dozwolonych pól
        filtered_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = self.get_serializer(instance, data=filtered_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)


class VendorAnalyticsView(APIView):
    """
    GET /vendor/analytics
    Statystyki sprzedaży dla produktów firmy dostawcy.
    """
    permission_classes = [permissions.IsAuthenticated, IsVendor]
    
    def get(self, request):
        vendor_company = request.user.vendor_company
        
        if not vendor_company:
            return Response({
                'error': 'Użytkownik nie jest przypisany do żadnej firmy dostawcy.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Pobierz produkty firmy vendora
        vendor_products = Product.objects.filter(vendor_company=vendor_company)
        
        if not vendor_products.exists():
            return Response({
                'message': 'Brak produktów dla tej firmy dostawcy.',
                'total_products': 0,
                'total_sales': 0,
                'total_revenue': 0,
                'products_sold': [],
                'monthly_sales': []
            })
        
        # Pobierz zamówienia zawierające produkty firmy vendora
        order_items = OrderItem.objects.filter(
            product__vendor_company=vendor_company,
            order__payment_status='paid'
        ).select_related('product', 'order')
        
        # Statystyki ogólne
        total_sales = order_items.aggregate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('price')
        )
        
        # Statystyki per produkt
        products_stats = order_items.values(
            'product__id', 'product__title', 'product__author'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum('price')
        ).order_by('-quantity_sold')[:10]
        
        # Sprzedaż miesięczna (ostatnie 12 miesięcy)
        twelve_months_ago = datetime.now() - timedelta(days=365)
        monthly_sales = order_items.filter(
            order__created_at__gte=twelve_months_ago
        ).annotate(
            month=TruncMonth('order__created_at')
        ).values('month').annotate(
            quantity=Sum('quantity'),
            revenue=Sum('price')
        ).order_by('month')
        
        # Formatuj dane miesięczne
        monthly_data = [
            {
                'month': item['month'].strftime('%Y-%m'),
                'quantity': item['quantity'],
                'revenue': float(item['revenue'])
            }
            for item in monthly_sales
        ]
        
        return Response({
            'vendor_company': vendor_company.name,
            'total_products': vendor_products.count(),
            'total_sales': total_sales['total_quantity'] or 0,
            'total_revenue': float(total_sales['total_revenue'] or 0),
            'products_sold': [
                {
                    'product_id': item['product__id'],
                    'title': item['product__title'],
                    'author': item['product__author'],
                    'quantity_sold': item['quantity_sold'],
                    'revenue': float(item['revenue'])
                }
                for item in products_stats
            ],
            'monthly_sales': monthly_data,
            'currency': 'PLN'
        })


class VendorDashboardView(APIView):
    """
    GET /vendor/dashboard
    Dashboard overview for vendor company.
    """
    permission_classes = [permissions.IsAuthenticated, IsVendor]
    
    def get(self, request):
        vendor_company = request.user.vendor_company
        
        if not vendor_company:
            return Response({
                'error': 'Użytkownik nie jest przypisany do żadnej firmy dostawcy.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Produkty firmy vendora
        vendor_products = Product.objects.filter(vendor_company=vendor_company)
        total_products = vendor_products.count()
        in_stock_products = vendor_products.filter(stock__gt=0).count()
        out_of_stock_products = vendor_products.filter(stock=0).count()
        
        # Ostatnie 30 dni
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_orders = OrderItem.objects.filter(
            product__vendor_company=vendor_company,
            order__payment_status='paid',
            order__created_at__gte=thirty_days_ago
        ).select_related('order')
        
        recent_sales = recent_orders.aggregate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('price')
        )
        
        return Response({
            'vendor_company': vendor_company.name,
            'vendor_email': request.user.email,
            'total_products': total_products,
            'in_stock_products': in_stock_products,
            'out_of_stock_products': out_of_stock_products,
            'last_30_days': {
                'sales': recent_sales['total_quantity'] or 0,
                'revenue': float(recent_sales['total_revenue'] or 0),
                'orders_count': recent_orders.values('order').distinct().count()
            },
            'currency': 'PLN'
        })
