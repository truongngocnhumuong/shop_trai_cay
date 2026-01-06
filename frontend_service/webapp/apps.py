import os
import sys
import atexit
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class WebappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webapp'

    def ready(self):
        """
        Called when Django starts up
        Register service with Consul if enabled
        """
        # Only register in main process (not in reloader or migration processes)
        run_main = os.environ.get('RUN_MAIN')
        if run_main != 'true':
            return
        
        # Don't register during migrations or other management commands
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return
        
        # Check if Consul is enabled
        from django.conf import settings
        use_consul = getattr(settings, 'USE_CONSUL', False)
        
        if not use_consul:
            return
        
        # Add root directory to path to find common package
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        try:
            from common.consul_client import get_consul_client
            consul_client = get_consul_client()
            
            if not consul_client.is_available():
                logger.warning("Consul server not available, skipping registration")
                return
            
            # Service configuration
            service_name = 'frontend-service'
            service_id = f"frontend-service-{os.getpid()}"
            service_port = 8000 # Default port for frontend
            service_address = getattr(settings, 'SERVICE_ADDRESS', 'localhost')
            health_check_url = f"http://{service_address}:{service_port}/health"
            
            # Register service
            success = consul_client.register_service(
                service_name=service_name,
                service_id=service_id,
                address=service_address,
                port=service_port,
                health_check_url=health_check_url,
                health_check_interval='10s'
            )
            
            if success:
                print(f"✅ Frontend Service registered with Consul (ID: {service_id})")
                logger.info(f"✓ Frontend Service registered with Consul (ID: {service_id})")
                
                # Deregister on shutdown
                def cleanup():
                    logger.info("Shutting down, deregistering from Consul...")
                    consul_client.deregister_service(service_id)
                
                atexit.register(cleanup)
            else:
                logger.warning("Failed to register with Consul")
                
        except Exception as e:
            logger.error(f"Error during Consul registration: {e}")

