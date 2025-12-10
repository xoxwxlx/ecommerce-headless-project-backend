from rest_framework import generics, permissions
from django.db.models import Q
from .models import Product
from .serializers import ProductSerializer


class ProductListView(generics.ListAPIView):
    """
    API endpoint to list all products.
    Supports filtering by genre using ?genre=fiction
    Supports filtering by format using ?format=ebook
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Product.objects.all()
        genre = self.request.query_params.get('genre', None)
        format_type = self.request.query_params.get('format', None)
        
        if genre:
            queryset = queryset.filter(genre=genre)
        
        if format_type:
            queryset = queryset.filter(format=format_type)
        
        return queryset


class BookListView(generics.ListAPIView):
    """
    API endpoint to list books (paperback and both formats).
    Supports filtering by genre using ?genre=fiction
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Product.objects.filter(Q(format='paperback') | Q(format='both'))
        genre = self.request.query_params.get('genre', None)
        
        if genre:
            queryset = queryset.filter(genre=genre)
        
        return queryset


class EbookListView(generics.ListAPIView):
    """
    API endpoint to list ebooks (ebook and both formats).
    Supports filtering by genre using ?genre=fiction
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Product.objects.filter(Q(format='ebook') | Q(format='both'))
        genre = self.request.query_params.get('genre', None)
        
        if genre:
            queryset = queryset.filter(genre=genre)
        
        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve a single product by ID.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
