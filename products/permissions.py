from rest_framework import permissions


class IsVendor(permissions.BasePermission):
    """
    Permission class to check if user is a vendor.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'vendor'


class IsVendorOwner(permissions.BasePermission):
    """
    Permission class to check if vendor's company owns the product.
    """
    def has_object_permission(self, request, view, obj):
        return (
            request.user.vendor_company and 
            obj.vendor_company == request.user.vendor_company
        )
