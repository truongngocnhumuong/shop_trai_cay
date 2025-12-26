from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404

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

