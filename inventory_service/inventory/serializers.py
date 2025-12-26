from rest_framework import serializers
from .models import Inventory
from .utils import get_product_from_service

class InventorySerializer(serializers.ModelSerializer):
    """Serializer for Inventory model"""
    product_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = ['id', 'product_id', 'product_info', 'quantity', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_product_info(self, obj):
        """Get product information from Product Service"""
        product_data = get_product_from_service(obj.product_id)
        if product_data:
            return {
                'id': product_data.get('id'),
                'name': product_data.get('name'),
                'category': product_data.get('category'),
                'price': product_data.get('price'),
            }
        return None

class InventoryUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating inventory
    
    Example JSON:
    {
        "product_id": 1,
        "quantity": 100
    }
    Or for bulk update:
    {
        "updates": [
            {"product_id": 1, "quantity": 100},
            {"product_id": 2, "quantity": 50}
        ]
    }
    """
    product_id = serializers.IntegerField(required=False, help_text="Product ID to update")
    quantity = serializers.IntegerField(min_value=0, required=False, help_text="New quantity value")
    updates = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="List of inventory updates for bulk operation"
    )
    
    def validate(self, attrs):
        """Validate that either single update or bulk update is provided"""
        has_single = attrs.get('product_id') is not None and attrs.get('quantity') is not None
        has_bulk = attrs.get('updates') is not None
        
        if not has_single and not has_bulk:
            raise serializers.ValidationError(
                "Either provide 'product_id' and 'quantity' for single update, "
                "or 'updates' list for bulk update."
            )
        
        if has_single and has_bulk:
            raise serializers.ValidationError(
                "Cannot provide both single update and bulk update at the same time."
            )
        
        return attrs
    
    def validate_product_id(self, value):
        """Validate that product exists in Product Service"""
        if value is not None:
            product = get_product_from_service(value)
            if not product:
                raise serializers.ValidationError(f"Product with ID {value} does not exist in Product Service.")
        return value

