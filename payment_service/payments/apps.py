import os
import sys
import atexit
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'

    def ready(self):
        """Register service with Consul if enabled"""
        run_main = os.environ.get('RUN_MAIN')
        if run_main != 'true':
            return
            
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return
            
        from django.conf import settings
        if not getattr(settings, 'USE_CONSUL', False):
            return
            
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        try:
            from common.consul_client import get_consul_client
            consul_client = get_consul_client()
            
            if not consul_client.is_available():
                return
                
            service_name = 'payment-service'
            service_id = f"payment-service-{os.getpid()}"
            service_port = 8006
            service_address = getattr(settings, 'SERVICE_ADDRESS', 'localhost')
            health_check_url = f"http://{service_address}:{service_port}/health"
            
            success = consul_client.register_service(
                service_name=service_name,
                service_id=service_id,
                address=service_address,
                port=service_port,
                health_check_url=health_check_url
            )
            
            if success:
                print(f"✅ Payment Service registered with Consul (ID: {service_id})")
                atexit.register(lambda: consul_client.deregister_service(service_id))
                
        except Exception as e:
            logger.error(f"Error during Consul registration: {e}")
