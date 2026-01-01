import requests
from django.conf import settings

def notify_inventory_service(product_id, action='create'):
    """
    Notify Inventory Service about product changes.
    - action='create': Triggers inventory record creation (initializes with 0 quantity)
    - action='delete': Deletes the inventory record for the product
    """
    url = f"{settings.INVENTORY_SERVICE_URL}/api/inventory/{product_id}/"
    
    try:
        if action == 'create':
            # GET will trigger get_or_create in inventory service
            response = requests.get(url, timeout=5)
        elif action == 'delete':
            # DELETE will remove the record
            response = requests.delete(url, timeout=5)
        
        if response.status_code in [200, 201, 204]:
            print(f"Successfully notified Inventory Service: {action} product {product_id}")
            return True
        else:
            print(f"Failed to notify Inventory Service: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error notifying Inventory Service: {str(e)}")
        return False
