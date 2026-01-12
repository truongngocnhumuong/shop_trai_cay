from rest_framework import serializers
from .models import Product
#xử lý URL ảnh:
class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category', 'image', 'image_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_url(self, obj):
        """Trả về full URL của ảnh nếu tồn tại"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None