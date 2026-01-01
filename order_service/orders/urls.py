from django.urls import path
from .views import (
    OrderItemDetailView,
    OrderListView,
    OrderDetailWebView,
    OrderCreateWebView,
    OrderListCreateView,
    OrderDetailView,
    OrderItemListView
)

urlpatterns = [
    path('', OrderListView.as_view(), name='order-list-web'),
    path('new/', OrderCreateWebView.as_view(), name='order-create-web'),
    path('web/<int:pk>/', OrderDetailWebView.as_view(), name='order-detail-web'),
    
    # API endpoints
    path('api/orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('api/orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('api/orders/<int:order_id>/items/', OrderItemListView.as_view(), name='order-item-list'),
    path('api/orders/<int:order_id>/items/<int:pk>/', OrderItemDetailView.as_view(), name='order-item-detail'),
]
