"""
Consul client utilities for service registration and discovery

This module provides a centralized way to interact with Consul for:
- Service registration with health checks
- Service discovery (finding healthy service instances)
- Graceful degradation when Consul is unavailable
"""
import consul
import os
import logging
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)


class ConsulClient:
    """
    Client for interacting with Consul service registry
    
    Usage:
        client = ConsulClient()
        client.register_service('my-service', 'my-service-1', 'localhost', 8000, 'http://localhost:8000/health')
        url = client.discover_service('other-service')
    """
    
    def __init__(self, host: str = 'localhost', port: int = 8500):
        """
        Initialize Consul client
        
        Args:
            host: Consul server host (default: localhost)
            port: Consul server port (default: 8500)
        """
        self.host = host
        self.port = port
        self.consul = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Consul connection with error handling"""
        try:
            self.consul = consul.Consul(host=self.host, port=self.port)
            # Test connection
            self.consul.agent.self()
            logger.info(f"Connected to Consul at {self.host}:{self.port}")
        except Exception as e:
            logger.warning(f"Failed to connect to Consul: {e}")
            self.consul = None
    
    def is_available(self) -> bool:
        """Check if Consul is available"""
        return self.consul is not None
    
    def register_service(
        self, 
        service_name: str, 
        service_id: str,
        address: str,
        port: int,
        health_check_url: str,
        health_check_interval: str = '10s',
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Register service with Consul
        
        Args:
            service_name: Logical name of the service (e.g., 'product-service')
            service_id: Unique ID for this instance (e.g., 'product-service-1')
            address: Service address (e.g., 'localhost')
            port: Service port (e.g., 8002)
            health_check_url: Full URL for health check (e.g., 'http://localhost:8002/health')
            health_check_interval: How often to check health (default: '10s')
            tags: Optional tags for the service
        
        Returns:
            True if registration successful, False otherwise
        """
        if not self.is_available():
            logger.warning("Consul not available, skipping registration")
            return False
        
        try:
            # Prepare tags
            service_tags = tags or []
            service_tags.append(os.getenv('ENVIRONMENT', 'development'))
            
            # SMARTER HEALTH CHECK: If the health check URL is localhost/127.0.0.1, 
            # and Consul is likely in Docker, it won't reach the service on host.
            # We'll use 'host.docker.internal' if available or the machine's actual IP.
            actual_check_url = health_check_url
            if 'localhost' in actual_check_url or '127.0.0.1' in actual_check_url:
                # If the service is on host and consul in docker, localhost fails.
                # 'host.docker.internal' is the standard way for docker-to-host.
                # We only change it for the check, not the service address.
                actual_check_url = actual_check_url.replace('localhost', 'host.docker.internal')
                actual_check_url = actual_check_url.replace('127.0.0.1', 'host.docker.internal')
                logger.debug(f"Adjusted health check URL for Docker: {actual_check_url}")
            
            # Register with health check
            self.consul.agent.service.register(
                name=service_name,
                service_id=service_id,
                address=address,
                port=port,
                check=consul.Check.http(
                    actual_check_url, 
                    interval=health_check_interval,
                    timeout='5s',
                    deregister='1h'  # INCREASED: Stay in list for 1 hour even if critical
                ),
                tags=service_tags
            )
            
            logger.info(
                f"✓ Registered service '{service_name}' (ID: {service_id}) "
                f"at {address}:{port} with Consul (Check: {actual_check_url})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service with Consul: {e}")
            return False
    
    def deregister_service(self, service_id: str) -> bool:
        """
        Deregister service from Consul
        
        Args:
            service_id: Unique ID of the service instance to deregister
        
        Returns:
            True if deregistration successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            self.consul.agent.service.deregister(service_id)
            logger.info(f"✓ Deregistered service '{service_id}' from Consul")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister service: {e}")
            return False
    
    def discover_service(self, service_name: str, tag: Optional[str] = None) -> Optional[str]:
        """
        Discover service URL from Consul (returns only healthy instances)
        
        Args:
            service_name: Name of the service to discover (e.g., 'product-service')
            tag: Optional tag to filter services
        
        Returns:
            Base URL of the service (e.g., 'http://localhost:8002') or None if not found
        """
        if not self.is_available():
            logger.warning(f"Consul not available, cannot discover '{service_name}'")
            return None
        
        try:
            # Query Consul for healthy instances
            index, services = self.consul.health.service(
                service_name, 
                passing=True,  # Only healthy instances
                tag=tag
            )
            
            if not services:
                logger.warning(f"No healthy instances found for service '{service_name}'")
                return None
            
            # Get first healthy instance (simple round-robin)
            # TODO: Implement proper load balancing if multiple instances
            service = services[0]
            address = service['Service']['Address']
            port = service['Service']['Port']
            
            url = f"http://{address}:{port}"
            logger.debug(f"Discovered '{service_name}' at {url}")
            
            return url
            
        except Exception as e:
            logger.error(f"Service discovery failed for '{service_name}': {e}")
            return None
    
    def get_all_services(self) -> Dict[str, List[Dict]]:
        """
        Get all registered services from Consul
        
        Returns:
            Dictionary mapping service names to list of instances
        """
        if not self.is_available():
            return {}
        
        try:
            services = self.consul.agent.services()
            return services
        except Exception as e:
            logger.error(f"Failed to get services from Consul: {e}")
            return {}
    
    def get_service_health(self, service_name: str) -> List[Tuple[str, str]]:
        """
        Get health status of all instances of a service
        
        Args:
            service_name: Name of the service
        
        Returns:
            List of tuples (service_id, status) where status is 'passing', 'warning', or 'critical'
        """
        if not self.is_available():
            return []
        
        try:
            index, checks = self.consul.health.service(service_name)
            results = []
            
            for check in checks:
                service_id = check['Service']['ID']
                # Get the health check status
                for health_check in check.get('Checks', []):
                    if health_check['ServiceID'] == service_id:
                        status = health_check['Status']
                        results.append((service_id, status))
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return []


# Singleton instance
_consul_client: Optional[ConsulClient] = None


def get_consul_client() -> ConsulClient:
    """
    Get or create Consul client singleton
    
    This ensures only one Consul connection is created per process.
    Configuration is read from environment variables:
    - CONSUL_HOST: Consul server host (default: localhost)
    - CONSUL_PORT: Consul server port (default: 8500)
    
    Returns:
        ConsulClient instance
    """
    global _consul_client
    
    if _consul_client is None:
        consul_host = os.getenv('CONSUL_HOST', 'localhost')
        consul_port = int(os.getenv('CONSUL_PORT', '8500'))
        _consul_client = ConsulClient(host=consul_host, port=consul_port)
    
    return _consul_client


def reset_consul_client():
    """Reset the singleton instance (useful for testing)"""
    global _consul_client
    _consul_client = None
