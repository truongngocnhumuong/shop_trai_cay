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
    """Get all products from Product Service via API"""
    try:
        url = f'{settings.PRODUCT_SERVICE_URL}/api/products/'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', data) if isinstance(data, dict) else data
        return []
    except Exception:
        return []

def verify_user_from_service(user_id):
    """
    Verify user exists in Auth Service via API
    Returns True if user exists, False otherwise
    """
    try:
        url = f'{settings.AUTH_SERVICE_URL}/api/users/{user_id}/'
        response = requests.get(url, timeout=5)
        return response.status_code == status.HTTP_200_OK
    except requests.exceptions.RequestException:
        return True

def get_user_info(user_id):
    """
    Get user information from Auth Service via API
    Returns user data or None if not found
    """
    try:
        url = f'{settings.AUTH_SERVICE_URL}/api/users/{user_id}/'
        response = requests.get(url, timeout=5)
        
        if response.status_code == status.HTTP_200_OK:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user {user_id}: {e}")
        return None

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

def get_all_inventories():
    """Get all inventory records from Inventory Service"""
    try:
        url = f'{settings.INVENTORY_SERVICE_URL}/api/inventory/'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', data) if isinstance(data, dict) else data
        return []
    except Exception:
        return []

def bulk_decrease_inventory(items_to_decrease):
    """
    Decrease inventory for multiple products in a single operation
    items_to_decrease: list of dicts {'product_id': id, 'quantity': q}
    """
    try:
        # 1. Get all current levels
        inventories = get_all_inventories()
        inventory_map = {item['product_id']: item['quantity'] for item in inventories}
        
        # 2. Prepare bulk update payload
        updates = []
        for item in items_to_decrease:
            pid = item['product_id']
            qty = item['quantity']
            current = inventory_map.get(pid, 0)
            new_qty = max(0, current - qty)
            updates.append({"product_id": pid, "quantity": new_qty})
        
        # 3. Call bulk update API
        url = f'{settings.INVENTORY_SERVICE_URL}/api/inventory/update/'
        response = requests.put(url, json={"updates": updates}, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error in bulk_decrease_inventory: {e}")
        return False
