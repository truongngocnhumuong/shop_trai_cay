from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.views import View
from django.contrib import messages

from .models import Inventory
from .serializers import InventorySerializer, InventoryUpdateSerializer, SimpleInventorySerializer
from .utils import get_product_from_service, get_all_products_from_service

class InventoryDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/inventory/{product_id}/ - Get inventory for a specific product
    """
    serializer_class = InventorySerializer
    lookup_field = 'product_id'
    lookup_url_kwarg = 'product_id'
    
    def get_queryset(self):
        return Inventory.objects.all()
    
    def get_object(self):
        product_id = self.kwargs.get('product_id')
        
        # Validate product exists in Product Service
        product = get_product_from_service(product_id)
        if not product:
            from rest_framework.exceptions import NotFound
            raise NotFound(f"Product with ID {product_id} does not exist in Product Service.")
        
        # Get or create inventory record
        inventory, created = Inventory.objects.get_or_create(
            product_id=product_id,
            defaults={'quantity': 0}
        )
        return inventory

class InventoryUpdateView(generics.GenericAPIView):
    """
    PUT /api/inventory/update/ - Update inventory quantity
    
    Single update:
    {
        "product_id": 1,
        "quantity": 100
    }
    
    Bulk update:
    {
        "updates": [
            {"product_id": 1, "quantity": 100},
            {"product_id": 2, "quantity": 50}
        ]
    }
    """
    serializer_class = InventoryUpdateSerializer
    
    def put(self, request, *args, **kwargs):
        serializer = InventoryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        # Single update
        if 'product_id' in validated_data and 'quantity' in validated_data:
            product_id = validated_data['product_id']
            quantity = validated_data['quantity']
            
            # Validate product exists
            product = get_product_from_service(product_id)
            if not product:
                return Response(
                    {'error': f'Product with ID {product_id} does not exist in Product Service.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create inventory
            inventory, created = Inventory.objects.get_or_create(
                product_id=product_id,
                defaults={'quantity': 0}
            )
            
            # Update quantity
            try:
                inventory.set_quantity(quantity)
                response_serializer = InventorySerializer(inventory)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Bulk update
        elif 'updates' in validated_data:
            updates = validated_data['updates']
            results = []
            errors = []
            
            # --- Bulk Update Optimization ---
            # Fetch all products once to avoid N+1 validation requests
            all_products = get_all_products_from_service()
            valid_product_ids = {p.get('id') for p in all_products}
            
            with transaction.atomic():
                for update_item in updates:
                    product_id = update_item.get('product_id')
                    quantity = update_item.get('quantity')
                    
                    if product_id is None or quantity is None:
                        continue
                        
                    # Bulk Validate product exists
                    if product_id not in valid_product_ids:
                        errors.append(f"Product with ID {product_id} does not exist.")
                        continue
                    
                    try:
                        inventory, created = Inventory.objects.get_or_create(
                            product_id=product_id,
                            defaults={'quantity': 0}
                        )
                        inventory.set_quantity(quantity)
                        results.append({
                            'product_id': product_id,
                            'quantity': inventory.quantity,
                            'status': 'success'
                        })
                    except ValueError as e:
                        errors.append(f"Product {product_id}: {str(e)}")
                    except Exception as e:
                        errors.append(f"Product {product_id}: {str(e)}")
            
            return Response({
                'success': len(errors) == 0,
                'updated': len(results),
                'results': results,
                'errors': errors
            }, status=status.HTTP_200_OK if len(errors) == 0 else status.HTTP_207_MULTI_STATUS)
        
        else:
            return Response(
                {'error': 'Invalid request data'},
                status=status.HTTP_400_BAD_REQUEST
            )

class InventoryListView(generics.ListAPIView):
    """
    GET /api/inventory/ - List all inventory records
    """
    queryset = Inventory.objects.all()
    serializer_class = SimpleInventorySerializer

# --- Web Interface Views ---

class InventoryDashboardView(View):
    def get(self, request):
        inventories = Inventory.objects.all()
        return render(request, 'dashboard.html', {'inventories': inventories})

class InventoryUpdatePageView(View):
    def get(self, request, product_id):
        inventory = get_object_or_404(Inventory, product_id=product_id)
        return render(request, 'update.html', {
            'product_id': product_id,
            'current_quantity': inventory.quantity
        })

class WebInventoryUpdateView(View):
    def post(self, request):
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity')
        
        try:
            inventory = get_object_or_404(Inventory, product_id=product_id)
            inventory.set_quantity(int(quantity))
            messages.success(request, f"Đã cập nhật tồn kho cho sản phẩm #{product_id} thành {quantity}.")
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
            
        return redirect('inventory_dashboard')

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
        
        # Check if we can query inventory table
        Inventory.objects.count()
        
        return Response({
            'status': 'healthy',
            'service': 'inventory-service',
            'version': '1.0.0',
            'checks': {
                'database': 'ok',
                'inventory_model': 'ok'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'service': 'inventory-service',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


