from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.db.models import Q

from .models import Product
from .serializers import ProductSerializer
from .utils import notify_inventory_service

class ProductListCreateView(generics.ListCreateAPIView):
    """
    GET /api/products/ - List all products
    POST /api/products/ - Create a new product
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def perform_create(self, serializer):
        """Notify inventory service after creating product via API"""
        product = serializer.save()
        notify_inventory_service(product.id, 'create')

    def get_serializer_context(self):
        """Thêm request vào context để tạo URL ảnh"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/products/{id}/ - Retrieve a product
    PUT /api/products/{id}/ - Update a product
    DELETE /api/products/{id}/ - Delete a product
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def perform_destroy(self, instance):
        """Notify inventory service before deleting product via API"""
        product_id = instance.id
        notify_inventory_service(product_id, 'delete')
        instance.delete()

    def get_serializer_context(self):
        """Add request to serializer context for image URL generation"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

# --- Web Interface Views ---

class ProductDashboardView(View):
    def get(self, request):
        products = Product.objects.all()
        return render(request, 'dashboard.html', {'products': products})

class ProductCreatePageView(View):
    def get(self, request):
        return render(request, 'product_form.html', {
            'categories': Product.CATEGORY_CHOICES
        })
    
    def post(self, request):
        name = request.POST.get('name')
        price = request.POST.get('price')
        category = request.POST.get('category')
        image = request.FILES.get('image') ## Lấy file ảnh từ form
        
        try:
            product = Product.objects.create(
                name=name,
                price=price,
                category=category,
                image=image # # Lưu ảnh
            )
            # Notify inventory service
            notify_inventory_service(product.id, 'create')
            
            messages.success(request, f"Đã thêm sản phẩm '{name}' thành công.")
            return redirect('product_dashboard')
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
            return render(request, 'product_form.html', {
                'categories': Product.CATEGORY_CHOICES
            })

class ProductUpdatePageView(View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return render(request, 'product_form.html', {
            'product': product,
            'categories': Product.CATEGORY_CHOICES
        })
    
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.category = request.POST.get('category')
        
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
            
        try:
            product.save()
            messages.success(request, f"Đã cập nhật sản phẩm '{product.name}' thành công.")
            return redirect('product_dashboard')
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
            return render(request, 'product_form.html', {
                'product': product,
                'categories': Product.CATEGORY_CHOICES
            })

class ProductDeleteWebView(View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        name = product.name
        # Notify inventory service before deleting
        notify_inventory_service(pk, 'delete')
        product.delete()
        messages.success(request, f"Đã xóa sản phẩm '{name}'.")
        return redirect('product_dashboard')

# --- Health Check for Consul ---

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for Consul monitoring
    
    Returns:
        200 OK if service is healthy
        503 Service Unavailable if service has issues
    """
    try:
        # Check database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check if we can query products table
        Product.objects.count()
        
        return Response({
            'status': 'healthy',
            'service': 'product-service',
            'version': '1.0.0',
            'checks': {
                'database': 'ok',
                'product_model': 'ok'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'service': 'product-service',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)