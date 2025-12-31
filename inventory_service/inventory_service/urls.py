from django.contrib import admin
from django.urls import path, include
from inventory.views import (
    InventoryDashboardView,
    InventoryUpdatePageView,
    WebInventoryUpdateView
)

urlpatterns = [
    # Web UI
    path('', InventoryDashboardView.as_view(), name='inventory_dashboard'),
    path('update/<int:product_id>/', InventoryUpdatePageView.as_view(), name='inventory_update_page'),
    path('web-update/', WebInventoryUpdateView.as_view(), name='web_inventory_update'),

    # API Endpoints
    path('admin/', admin.site.urls),
    path('api/inventory/', include('inventory.urls')),
]
