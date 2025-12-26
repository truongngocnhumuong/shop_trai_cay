from rest_framework import serializers
from .models import Order, OrderItem
from .utils import get_product_from_service

class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model"""
    product_info = serializers.SerializerMethodField()
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_info', 'quantity', 'price', 'subtotal', 'created_at']
        read_only_fields = ['id', 'price', 'created_at']
    
    def get_product_info(self, obj):
        """Get product information from Product Service"""
        product_data = get_product_from_service(obj.product_id)
        if product_data:
            return {
                'id': product_data.get('id'),
                'name': product_data.get('name'),
                'category': product_data.get('category'),
                'image_url': product_data.get('image_url'),
            }
        return None

class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating OrderItem (without product_info)"""
    product_id = serializers.IntegerField(
        help_text="ID của sản phẩm từ Product Service (port 8002)"
    )
    quantity = serializers.IntegerField(
        min_value=1,
        help_text="Số lượng sản phẩm (tối thiểu 1)"
    )
    
    class Meta:
        model = OrderItem
        fields = ['product_id', 'quantity']
    
    def validate_product_id(self, value):
        """Validate that product exists in Product Service"""
        product = get_product_from_service(value)
        if not product:
            raise serializers.ValidationError(f"Product with ID {value} does not exist in Product Service.")
        return value

class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""
    order_items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user_id', 'total_price', 'status', 'order_items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']

class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating Order with OrderItems
    
    Example JSON:
    {
        "user_id": 1,
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 3}
        ]
    }
    """
    user_id = serializers.IntegerField(
        help_text="ID của người dùng từ Auth Service (port 8001)"
    )
    items = OrderItemCreateSerializer(
        many=True,
        help_text="Danh sách các sản phẩm trong đơn hàng. Sử dụng tab 'Raw data' để nhập JSON."
    )
    
    def validate_items(self, value):
        """Validate that items list is not empty"""
        if not value:
            raise serializers.ValidationError("Order must have at least one item.")
        return value
    
    def create(self, validated_data):
        """Create Order and OrderItems"""
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        
        total_price = 0
        for item_data in items_data:
            product_id = item_data['product_id']
            quantity = item_data['quantity']
            
            # Get product price from Product Service
            product = get_product_from_service(product_id)
            if not product:
                raise serializers.ValidationError(f"Product {product_id} not found in Product Service.")
            
            price = float(product['price'])
            OrderItem.objects.create(
                order=order,
                product_id=product_id,
                quantity=quantity,
                price=price
            )
            total_price += price * quantity
        
        order.total_price = total_price
        order.save()
        
        return order

