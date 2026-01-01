from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.db.models import Q

from .models import Product
from .serializers import ProductSerializer

class ProductListCreateView(generics.ListCreateAPIView):
    """
    GET /api/products/ - List all products
    POST /api/products/ - Create a new product
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_serializer_context(self):
        """Add request to serializer context for image URL generation"""
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
        image = request.FILES.get('image')
        
        try:
            Product.objects.create(
                name=name,
                price=price,
                category=category,
                image=image
            )
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
        product.delete()
        messages.success(request, f"Đã xóa sản phẩm '{name}'.")
        return redirect('product_dashboard')

