from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price', 'created_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user_id']
    ordering = ['-created_at']
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product_id', 'quantity', 'price', 'subtotal', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product_id', 'order__id']
    ordering = ['-created_at']

