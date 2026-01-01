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
    path('api/', OrderListCreateView.as_view(), name='order-list-create'),
    path('api/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('api/<int:order_id>/items/', OrderItemListView.as_view(), name='order-item-list'),
    path('api/<int:order_id>/items/<int:pk>/', OrderItemDetailView.as_view(), name='order-item-detail'),
]
