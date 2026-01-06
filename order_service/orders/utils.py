"""
Utility functions for communicating with other services
"""
import requests
import sys
import os
import logging
from django.conf import settings
from rest_framework import status

logger = logging.getLogger(__name__)

# Add common module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def get_service_url(service_name):
    """
    Get service URL using Consul discovery or fallback to hardcoded URL
    
    Args:
        service_name: Name of the service (e.g., 'product-service', 'auth-service')
    
    Returns:
        Base URL of the service (e.g., 'http://localhost:8002')
    """
    # Try Consul discovery if enabled
    if getattr(settings, 'USE_CONSUL', False):
        try:
            from common.consul_client import get_consul_client
            
            consul_client = get_consul_client()
            url = consul_client.discover_service(service_name)
            
            if url:
                logger.debug(f"Discovered {service_name} via Consul: {url}")
                return url
            else:
                logger.warning(f"Consul discovery failed for {service_name}, using fallback")
        except Exception as e:
            logger.warning(f"Error during Consul discovery for {service_name}: {e}, using fallback")
    
    # Fallback to hardcoded URLs from settings
    fallback_map = {
        'product-service': settings.PRODUCT_SERVICE_URL,
        'auth-service': settings.AUTH_SERVICE_URL,
        'inventory-service': settings.INVENTORY_SERVICE_URL,
    }
    
    fallback_url = fallback_map.get(service_name, '')
    logger.debug(f"Using fallback URL for {service_name}: {fallback_url}")
    return fallback_url


def get_product_from_service(product_id):
    """
    Get product information from Product Service via API
    Returns product data or None if not found
    """
    try:
        base_url = get_service_url('product-service')
        url = f'{base_url}/api/products/{product_id}/'
        response = requests.get(url, timeout=5)
        
        if response.status_code == status.HTTP_200_OK:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        return None

def get_all_products_from_service():
    """Get all products from Product Service via API"""
    try:
        base_url = get_service_url('product-service')
        url = f'{base_url}/api/products/'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', data) if isinstance(data, dict) else data
        return []
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return []

def verify_user_from_service(user_id):
    """
    Verify user exists in Auth Service via API
    Returns True if user exists, False otherwise
    """
    try:
        base_url = get_service_url('auth-service')
        url = f'{base_url}/api/users/{user_id}/'
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
        base_url = get_service_url('auth-service')
        url = f'{base_url}/api/users/{user_id}/'
        response = requests.get(url, timeout=5)
        
        if response.status_code == status.HTTP_200_OK:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None

def get_inventory(product_id):
    """
    Get current inventory for a product from Inventory Service
    Returns inventory data or None if not found
    """
    try:
        base_url = get_service_url('inventory-service')
        url = f'{base_url}/api/inventory/{product_id}/'
        response = requests.get(url, timeout=5)
        
        if response.status_code == status.HTTP_200_OK:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching inventory for product {product_id}: {e}")
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
            logger.error(f"Could not fetch inventory for product {product_id}")
            return False
        
        current_quantity = inventory.get('quantity', 0)
        new_quantity = current_quantity - quantity
        
        if new_quantity < 0:
            logger.warning(f"Insufficient inventory for product {product_id}. Available: {current_quantity}, Requested: {quantity}")
            return False
        
        # Update inventory
        base_url = get_service_url('inventory-service')
        url = f'{base_url}/api/inventory/update/'
        response = requests.put(url, json={
            'product_id': product_id,
            'quantity': new_quantity
        }, timeout=5)
        
        if response.status_code == status.HTTP_200_OK:
            return True
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error decreasing inventory for product {product_id}: {e}")
        return False

def get_all_inventories():
    """Get all inventory records from Inventory Service"""
    try:
        base_url = get_service_url('inventory-service')
        url = f'{base_url}/api/inventory/'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', data) if isinstance(data, dict) else data
        return []
    except Exception as e:
        logger.error(f"Error fetching inventories: {e}")
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
        base_url = get_service_url('inventory-service')
        url = f'{base_url}/api/inventory/update/'
        response = requests.put(url, json={"updates": updates}, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error in bulk_decrease_inventory: {e}")
        return False
