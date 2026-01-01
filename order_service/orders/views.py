from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from rest_framework import status, generics
from rest_framework.response import Response

from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderItemSerializer
)
from .utils import get_product_from_service, get_all_products_from_service, get_user_info

class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET /api/orders/ - List all orders
    POST /api/orders/ - Create a new order
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
    """
    serializer_class = OrderItemSerializer
    
    def get_queryset(self):
        order_id = self.kwargs['order_id']
        return OrderItem.objects.filter(order_id=order_id)
    
    def update(self, request, *args, **kwargs):
        """Update order item and recalculate order total"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if 'quantity' in request.data:
            product = get_product_from_service(instance.product_id)
            if product:
                request.data['price'] = product['price']
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        instance.order.calculate_total()
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Delete order item and recalculate order total"""
        instance = self.get_object()
        order = instance.order
        self.perform_destroy(instance)
        order.calculate_total()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Web Interface Views ---

class OrderListView(View):
    def get(self, request):
        orders = Order.objects.all().order_by('-created_at')
        
        # Enrich orders with usernames
        # Optimization: cache user info to avoid duplicate requests
        user_cache = {}
        for order in orders:
            if order.user_id not in user_cache:
                user_data = get_user_info(order.user_id)
                user_cache[order.user_id] = user_data.get('username', f"User {order.user_id}") if user_data else f"User {order.user_id}"
            
            order.username = user_cache[order.user_id]
            
        return render(request, 'orders/order_list.html', {'orders': orders})

class OrderDetailWebView(View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        
        # Enrich order with username
        user_data = get_user_info(order.user_id)
        order.username = user_data.get('username', f"User {order.user_id}") if user_data else f"User {order.user_id}"
        
        # Enrich order items with product info - CREATE A LIST to prevent re-query in template
        items = list(order.order_items.all())
        for item in items:
            product_data = get_product_from_service(item.product_id)
            if product_data:
                item.product_info = {
                    'name': product_data.get('name'),
                    # Use 'image_url' from serializer or fallback to 'image'
                    'image_url': product_data.get('image_url') or product_data.get('image'),
                }
            else:
                item.product_info = None
                
        return render(request, 'orders/order_detail.html', {
            'order': order,
            'items': items
        })
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"Đã cập nhật trạng thái đơn hàng #{order.id} thành {order.get_status_display()}.")
        return redirect('order-detail-web', pk=pk)

class OrderCreateWebView(View):
    def get(self, request):
        products = get_all_products_from_service()
        return render(request, 'orders/order_form.html', {'products': products})
    
    def post(self, request):
        user_id = request.POST.get('user_id')
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        
        items = []
        for pid, qty in zip(product_ids, quantities):
            if pid and qty:
                items.append({'product_id': int(pid), 'quantity': int(qty)})
        
        if not items:
            messages.error(request, "Vui lòng chọn ít nhất một sản phẩm.")
            return self.get(request)
            
        serializer = OrderCreateSerializer(data={
            'user_id': user_id,
            'items': items
        })
        
        if serializer.is_valid():
            order = serializer.save()
            messages.success(request, f"Đặt hàng thành công! Mã đơn hàng: #{order.id}")
            return redirect('order-list-web')
        else:
            error_msg = str(serializer.errors)
            messages.error(request, f"Lỗi khi đặt hàng: {error_msg}")
            return self.get(request)
