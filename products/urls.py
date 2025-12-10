from django.urls import path
from .views import ProductListView, ProductDetailView, BookListView, EbookListView

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('books/', BookListView.as_view(), name='book-list'),
    path('ebooks/', EbookListView.as_view(), name='ebook-list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]
