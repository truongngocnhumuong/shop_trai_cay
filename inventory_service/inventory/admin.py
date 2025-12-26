from django.contrib import admin
from .models import Inventory

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'product_id', 'quantity', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['product_id']
    ordering = ['product_id']
    readonly_fields = ['created_at', 'updated_at']

