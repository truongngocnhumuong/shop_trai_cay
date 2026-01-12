#Chứa các hàm tiện ích để giao tiếp giữa các service
import time
import requests
import sys
import os
import logging
from django.conf import settings
from django.contrib import messages

logger = logging.getLogger(__name__)

# Add common module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def get_service_url(service_name):
    """
    Get service URL - Prefer API Gateway for all backend requests
    """
    # Prefer Gateway for all service calls from frontend
    gateway_url = getattr(settings, 'GATEWAY_URL', 'http://localhost:8005')
    
    # We could still use Consul to find the Gateway itself if it's dynamic
    if getattr(settings, 'USE_CONSUL', False):
        try:
            from common.consul_client import get_consul_client
            consul_client = get_consul_client()
            discovered_gateway = consul_client.discover_service('gateway-service')
            if discovered_gateway:
                return discovered_gateway
        except Exception as e:
            logger.warning(f"Consul discovery failed for gateway-service: {e}")

    return gateway_url


def call_auth_service_login(username, password):
    """Call Auth Service to login user"""
    try:
        base_url = get_service_url('auth-service')
        # Use /api/auth/ prefix for Gateway to route correctly to Auth Service
        url = f'{base_url}/api/auth/login/'
        response = requests.post(url, json={
            'username': username,
            'password': password
        }, timeout=5)
        
        if response.status_code == 200:
            return {
                'success': True,
                'data': response.json()
            }
        else:
            return {
                'success': False,
                'error': response.json().get('detail', 'Login failed')
            }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Cannot connect to Auth Service: {str(e)}'
        }

def call_auth_service_verify_token(token):
    """Call Auth Service to verify token"""
    try:
        base_url = get_service_url('auth-service')
        # Use /api/auth/ prefix for Gateway
        url = f'{base_url}/api/auth/verify-token/'
        response = requests.post(url, json={'token': token}, timeout=5)
        
        if response.status_code == 200:
            return {
                'success': True,
                'data': response.json()
            }
        return {
            'success': False,
            'error': 'Invalid token'
        }
    except requests.exceptions.RequestException:
        return {
            'success': False,
            'error': 'Cannot connect to Auth Service'
        }

def get_products():
    """Get all products from Product Service"""
    try:
        # Add timestamp to prevent caching
        timestamp = int(time.time())
        base_url = get_service_url('product-service')
        url = f'{base_url}/api/products/'
        params = {'_': timestamp}  # Prevent caching
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # Handle both direct array response and paginated response with 'results' key
            products = data.get('results', data) if isinstance(data, dict) else data
            return {
                'success': True,
                'data': products
            }
        return {
            'success': False,
            'error': 'Failed to fetch products'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Cannot connect to Product Service: {str(e)}'
        }

def get_product(product_id):
    """Get a single product from Product Service"""
    try:
        base_url = get_service_url('product-service')
        url = f'{base_url}/api/products/{product_id}/'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            return {
                'success': True,
                'data': response.json()
            }
        return {
            'success': False,
            'error': 'Product not found'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Cannot connect to Product Service: {str(e)}'
        }

def get_inventory(product_id):
    """Get inventory for a product from Inventory Service"""
    try:
        # Call the correct endpoint with product_id as path parameter
        base_url = get_service_url('inventory-service')
        url = f'{base_url}/api/inventory/{product_id}/'
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'data': data
            }
        elif response.status_code == 404:
            return {
                'success': False,
                'error': f'No inventory found for product {product_id}'
            }
        else:
            return {
                'success': False,
                'error': f'Failed to fetch inventory. Status code: {response.status_code}'
            }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Cannot connect to Inventory Service: {str(e)}'
        }

def get_all_inventories():
    """Get all inventory records from Inventory Service"""
    try:
        base_url = get_service_url('inventory-service')
        url = f'{base_url}/api/inventory/'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # Handle paginated or direct list response
            inventories = data.get('results', data) if isinstance(data, dict) else data
            return {
                'success': True,
                'data': inventories
            }
        return {
            'success': False,
            'error': 'Failed to fetch all inventories'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Cannot connect to Inventory Service: {str(e)}'
        }

def create_order(user_id, items, access_token=None):
    """Create order via Order Service"""
    try:
        base_url = get_service_url('order-service')
        url = f'{base_url}/api/orders/'
        headers = {'Content-Type': 'application/json'}
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'
        
        # Increase timeout and add connection pooling
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=10
        )
        session.mount('http://', adapter)
        
        response = session.post(
            url,
            json={
                'user_id': user_id,
                'items': items
            },
            headers=headers,
            timeout=30  # Increased timeout to 30 seconds
        )
        
        if response.status_code == 201:
            return {
                'success': True,
                'data': response.json()
            }
        else:
            # Check if response is JSON
            try:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('detail', 'Failed to create order')
            except ValueError:
                # If not JSON (e.g. HTML 404 page), provide a better message
                error_msg = f"Order Service returned an unexpected response (Status {response.status_code})."
                if response.status_code == 404:
                    error_msg = "Order Service endpoint not found (404). Please check service configuration."
                
            return {
                'success': False,
                'error': error_msg,
                'status_code': response.status_code
            }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Cannot connect to Order Service: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }