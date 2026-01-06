from django.contrib import admin
from django.urls import path, include
from orders.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('orders.urls')),
    
    # Health check for Consul
    path('health', health_check, name='health_check'),
]

