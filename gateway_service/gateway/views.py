import requests
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import sys
import os

logger = logging.getLogger(__name__)

# Add common module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def get_service_url(service_name):
    """Get service URL using Consul discovery or fallback to hardcoded URL"""
    if getattr(settings, 'USE_CONSUL', False):
        try:
            from common.consul_client import get_consul_client
            consul_client = get_consul_client()
            url = consul_client.discover_service(service_name)
            if url:
                return url
        except Exception as e:
            logger.warning(f"Consul discovery failed for {service_name}: {e}")
    
    fallback_map = {
        'auth-service': settings.AUTH_SERVICE_URL,
        'product-service': settings.PRODUCT_SERVICE_URL,
        'order-service': settings.ORDER_SERVICE_URL,
        'inventory-service': settings.INVENTORY_SERVICE_URL,
        'payment-service': settings.PAYMENT_SERVICE_URL,
    }
    return fallback_map.get(service_name, '')

@csrf_exempt
def proxy_view(request, service_name, path):
    """
    Proxy request to the appropriate backend service
    """
    service_map = {
        'auth': 'auth-service',
        'products': 'product-service',
        'orders': 'order-service',
        'inventory': 'inventory-service',
        'payments': 'payment-service',
        'payments_ui': 'payment-service',
    }
    
    # Mapping between gateway service name and backend API prefix
    # Auth backend doesn't use 'auth/' prefix in URLs
    prefix_map = {
        'auth': '',  
        'products': 'products/',
        'orders': 'orders/',
        'inventory': 'inventory/',
        'payments': 'payments/',
        'payments_ui': 'checkout/',
    }
    
    target_service = service_map.get(service_name)
    if not target_service:
        return JsonResponse({'error': f'Service mapping for "{service_name}" not found'}, status=404)
        
    base_url = get_service_url(target_service)
    if not base_url:
        logger.error(f"Discovery failed for {target_service}")
        return JsonResponse({'error': f'Could not discover service: {target_service}'}, status=503)
        
    # Construct target URL
    # Backend services usually have URLs like: http://host:port/api/products/...
    # But auth-service has: http://host:port/api/login/ (no 'auth' segment)
    backend_prefix = prefix_map.get(service_name, f"{service_name}/")
    target_url = f"{base_url}/api/{backend_prefix}{path}"
    
    # Clean up double slashes if any
    target_url = target_url.replace('//api', '/api').replace('api//', 'api/')
    
    logger.info(f"Proxying {request.method} {request.path} -> {target_url}")
        
    # Copy headers
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']}
    
    try:
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.body,
            params=request.GET,
            timeout=30,
            allow_redirects=False
        )
        
        logger.info(f"Backend responded with status {response.status_code}")
        
        # Return response from backend service
        django_response = HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
        
        # Copy backend headers back to frontend (excluding some)
        for k, v in response.headers.items():
            if k.lower() not in ['content-encoding', 'transfer-encoding', 'content-length', 'connection']:
                django_response[k] = v
                
        return django_response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy connection error calling {target_url}: {e}")
        return JsonResponse({'error': f'Backend service connectivity error: {str(e)}'}, status=502)

def health_check(request):
    return JsonResponse({
        "status": "healthy",
        "service": "gateway-service",
        "version": "1.0.0"
    })
