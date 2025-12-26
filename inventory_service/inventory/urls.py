from django.urls import path
from .views import (
    InventoryDetailView,
    InventoryUpdateView,
    InventoryListView
)

urlpatterns = [
    path('', InventoryListView.as_view(), name='inventory-list'),
    path('update/', InventoryUpdateView.as_view(), name='inventory-update'),
    path('<int:product_id>/', InventoryDetailView.as_view(), name='inventory-detail'),
]

