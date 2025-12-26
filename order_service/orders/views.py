from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404

from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderItemSerializer
)
from .utils import get_product_from_service

class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET /api/orders/ - List all orders
    
    POST /api/orders/ - Create a new order
    
    **Request Body Example:**
    ```json
    {
        "user_id": 1,
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 3}
        ]
    }
    ```
    
    **Note:** Sử dụng tab "Raw data" để nhập JSON. HTML form không hỗ trợ nested lists.
    """
    queryset = Order.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        """Create order with items"""
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()
            response_serializer = OrderSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/orders/{id}/ - Retrieve an order
    PUT /api/orders/{id}/ - Update an order
    DELETE /api/orders/{id}/ - Delete an order
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    
    def update(self, request, *args, **kwargs):
        """Update order (mainly status)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class OrderItemListView(generics.ListAPIView):
    """
    GET /api/orders/{order_id}/items/ - List all items in an order
    """
    serializer_class = OrderItemSerializer
    
    def get_queryset(self):
        order_id = self.kwargs['order_id']
        return OrderItem.objects.filter(order_id=order_id)

class OrderItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/orders/{order_id}/items/{id}/ - Retrieve an order item
    PUT /api/orders/{order_id}/items/{id}/ - Update an order item
    DELETE /api/orders/{order_id}/items/{id}/ - Delete an order item
    """
    serializer_class = OrderItemSerializer
    
    def get_queryset(self):
        order_id = self.kwargs['order_id']
        return OrderItem.objects.filter(order_id=order_id)
    
    def update(self, request, *args, **kwargs):
        """Update order item and recalculate order total"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # If quantity is being updated, get current product price
        if 'quantity' in request.data:
            product = get_product_from_service(instance.product_id)
            if product:
                request.data['price'] = product['price']
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Recalculate order total
        instance.order.calculate_total()
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Delete order item and recalculate order total"""
        instance = self.get_object()
        order = instance.order
        self.perform_destroy(instance)
        
        # Recalculate order total
        order.calculate_total()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

