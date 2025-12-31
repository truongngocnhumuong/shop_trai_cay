"""
Utility functions for communicating with other services
"""
import requests
from django.conf import settings
from rest_framework import status

def get_product_from_service(product_id):
    """
    Get product information from Product Service via API
    Returns product data or None if not found
    """
    try:
        url = f'{settings.PRODUCT_SERVICE_URL}/api/products/{product_id}/'
        response = requests.get(url, timeout=5)
        
        if response.status_code == status.HTTP_200_OK:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching product {product_id}: {e}")
        return None

def get_all_products_from_service():
    """
    Get all products from Product Service via API
    Returns list of products or empty list if failed
    """
    try:
        url = f'{settings.PRODUCT_SERVICE_URL}/api/products/'
        response = requests.get(url, timeout=5)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            return data.get('results', data) if isinstance(data, dict) else data
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching all products: {e}")
        return []

def update_inventory_from_order(order_data):
    """
    Update inventory based on order data from Order Service
    This function can be called by Order Service after creating an order
    
    Args:
        order_data: Dictionary containing order information with items
            Example: {
                'items': [
                    {'product_id': 1, 'quantity': 2},
                    {'product_id': 2, 'quantity': 3}
                ]
            }
    
    Returns:
        dict: Result of inventory update
    """
    from .models import Inventory
    
    results = []
    errors = []
    
    for item in order_data.get('items', []):
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        
        if not product_id or not quantity:
            errors.append(f"Invalid item data: {item}")
            continue
        
        try:
            inventory, created = Inventory.objects.get_or_create(
                product_id=product_id,
                defaults={'quantity': 0}
            )
            
            # Decrease inventory when order is created
            inventory.decrease(quantity)
            
            results.append({
                'product_id': product_id,
                'quantity_after': inventory.quantity,
                'status': 'success'
            })
        except ValueError as e:
            errors.append(f"Product {product_id}: {str(e)}")
        except Exception as e:
            errors.append(f"Product {product_id}: {str(e)}")
    
    return {
        'success': len(errors) == 0,
        'results': results,
        'errors': errors
    }

