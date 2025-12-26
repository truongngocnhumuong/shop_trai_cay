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

