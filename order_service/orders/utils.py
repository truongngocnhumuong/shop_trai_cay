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

def verify_user_from_service(user_id):
    """
    Verify user exists in Auth Service via API
    Returns True if user exists, False otherwise
    """
    try:
        # Note: This assumes Auth Service has a user verification endpoint
        # If not available, we can skip this check or implement it later
        url = f'{settings.AUTH_SERVICE_URL}/api/users/{user_id}/'
        response = requests.get(url, timeout=5)
        return response.status_code == status.HTTP_200_OK
    except requests.exceptions.RequestException:
        # If service is unavailable, we'll allow the order to proceed
        # In production, you might want to handle this differently
        return True

def get_inventory(product_id):
    """
    Get current inventory for a product from Inventory Service
    Returns inventory data or None if not found
    """
    try:
        url = f'{settings.INVENTORY_SERVICE_URL}/api/inventory/{product_id}/'
        response = requests.get(url, timeout=5)
        
        if response.status_code == status.HTTP_200_OK:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching inventory for product {product_id}: {e}")
        return None

def decrease_inventory(product_id, quantity):
    """
    Decrease inventory for a product via Inventory Service API
    Returns True if successful, False otherwise
    """
    try:
        # Get current inventory
        inventory = get_inventory(product_id)
        if not inventory:
            print(f"Could not fetch inventory for product {product_id}")
            return False
        
        current_quantity = inventory.get('quantity', 0)
        new_quantity = current_quantity - quantity
        
        if new_quantity < 0:
            print(f"Insufficient inventory for product {product_id}. Available: {current_quantity}, Requested: {quantity}")
            return False
        
        # Update inventory
        url = f'{settings.INVENTORY_SERVICE_URL}/api/inventory/update/'
        response = requests.put(url, json={
            'product_id': product_id,
            'quantity': new_quantity
        }, timeout=5)
        
        if response.status_code == status.HTTP_200_OK:
            return True
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error decreasing inventory for product {product_id}: {e}")
        return False

