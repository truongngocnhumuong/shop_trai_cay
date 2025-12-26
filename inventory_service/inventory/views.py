from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Inventory
from .serializers import InventorySerializer, InventoryUpdateSerializer
from .utils import get_product_from_service

class InventoryDetailView(generics.RetrieveAPIView):
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
            
            with transaction.atomic():
                for update_item in updates:
                    product_id = update_item.get('product_id')
                    quantity = update_item.get('quantity')
                    
                    if product_id is None or quantity is None:
                        errors.append(f"Invalid update item: {update_item}")
                        continue
                    
                    # Validate product exists
                    product = get_product_from_service(product_id)
                    if not product:
                        errors.append(f"Product {product_id} does not exist in Product Service.")
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
    serializer_class = InventorySerializer

