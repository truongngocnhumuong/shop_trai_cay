from django.contrib import admin
from django.urls import path, re_path
from gateway.views import proxy_view, health_check

urlpatterns = [
    path('admin/', admin.site.urls), # Fixed typo: changed .length to .urls
    path('health/', health_check, name='health_check'),
    
    # Auth Service proxy
    re_path(r'^api/auth/(?P<path>.*)$', proxy_view, {'service_name': 'auth'}, name='auth_proxy'),
    
    # Product Service proxy
    re_path(r'^api/products/(?P<path>.*)$', proxy_view, {'service_name': 'products'}, name='product_proxy'),
    
    # Order Service proxy
    re_path(r'^api/orders/(?P<path>.*)$', proxy_view, {'service_name': 'orders'}, name='order_proxy'),
    
    # Inventory Service proxy
    re_path(r'^api/inventory/(?P<path>.*)$', proxy_view, {'service_name': 'inventory'}, name='inventory_proxy'),
    
    # Payment Service proxy
    re_path(r'^api/payments/(?P<path>.*)$', proxy_view, {'service_name': 'payments'}, name='payment_proxy'),
    
    # Payment UI (Direct)
    re_path(r'^checkout/(?P<path>.*)$', proxy_view, {'service_name': 'payments_ui'}, name='payment_ui_proxy'),
]
