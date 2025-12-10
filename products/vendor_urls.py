from django.urls import path
from .vendor_views import (
    VendorProductListView,
    VendorProductDetailView,
    VendorAnalyticsView,
    VendorDashboardView
)

urlpatterns = [
    path('products/', VendorProductListView.as_view(), name='vendor-product-list'),
    path('products/<int:pk>/', VendorProductDetailView.as_view(), name='vendor-product-detail'),
    path('analytics/', VendorAnalyticsView.as_view(), name='vendor-analytics'),
    path('dashboard/', VendorDashboardView.as_view(), name='vendor-dashboard'),
]
