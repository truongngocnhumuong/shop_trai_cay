import requests
import logging
from django.conf import settings
import sys
import os

logger = logging.getLogger(__name__)

# Add common module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def get_service_url(service_name):
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
        'order-service': settings.ORDER_SERVICE_URL,
    }
    return fallback_map.get(service_name, '')

def update_order_payment_status(order_id, status):
    """
    Update order payment status in Order Service
    status: 'paid', 'failed', 'pending'
    """
    try:
        base_url = get_service_url('order-service')
        url = f"{base_url}/api/orders/{order_id}/payment-status/"
        response = requests.patch(url, json={'payment_status': status}, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error updating order {order_id} payment status: {e}")
        return False
