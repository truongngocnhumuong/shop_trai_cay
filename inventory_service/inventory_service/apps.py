"""
Django app configuration for Inventory Service with Consul integration
"""
import sys
import os
import atexit
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class InventoryServiceConfig(AppConfig):
    """Inventory Service application configuration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory_service'
    
    def ready(self):
        """Register service with Consul if enabled"""
        print("[DEBUG] InventoryServiceConfig.ready() called")
        
        run_main = os.environ.get('RUN_MAIN')
        print(f"[DEBUG] RUN_MAIN = {run_main}")
        
        if run_main != 'true':
            print("[DEBUG] Skipping Consul registration (not main process)")
            return
        
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            print("[DEBUG] Skipping Consul registration (migration command)")
            return
        
        from django.conf import settings
        use_consul = getattr(settings, 'USE_CONSUL', False)
        
        print(f"[DEBUG] USE_CONSUL setting = {use_consul}")
        print(f"[DEBUG] USE_CONSUL env = {os.getenv('USE_CONSUL')}")
        
        if not use_consul:
            print("⚠️  Consul integration disabled (USE_CONSUL=False)")
            logger.info("Consul integration disabled")
            return
        
        print("[DEBUG] Proceeding with Consul registration...")
        
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        try:
            from common.consul_client import get_consul_client
            
            print("[DEBUG] Getting Consul client...")
            consul_client = get_consul_client()
            
            if not consul_client.is_available():
                print("⚠️  Consul server not available, skipping registration")
                logger.warning("Consul server not available")
                return
            
            print("[DEBUG] Consul client is available!")
            
            service_name = 'inventory-service'
            service_id = f"inventory-service-{os.getpid()}"
            service_port = 8004
            service_address = getattr(settings, 'SERVICE_ADDRESS', 'localhost')
            health_check_url = f"http://{service_address}:{service_port}/health"
            
            print(f"[DEBUG] Registering service: {service_name}")
            print(f"[DEBUG] Service ID: {service_id}")
            print(f"[DEBUG] Address: {service_address}:{service_port}")
            print(f"[DEBUG] Health check URL: {health_check_url}")
            
            success = consul_client.register_service(
                service_name=service_name,
                service_id=service_id,
                address=service_address,
                port=service_port,
                health_check_url=health_check_url
            )
            
            if success:
                print(f"✅ Inventory Service registered with Consul (ID: {service_id})")
                logger.info(f"✓ Inventory Service registered with Consul (ID: {service_id})")
                
                def cleanup():
                    print("Shutting down, deregistering from Consul...")
                    consul_client.deregister_service(service_id)
                
                atexit.register(cleanup)
                
        except Exception as e:
            print(f"❌ Error during Consul registration: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error during Consul registration: {e}")
