from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from products.views import (
    ProductDashboardView,
    ProductCreatePageView,
    ProductUpdatePageView,
    ProductDeleteWebView,
    health_check
)

urlpatterns = [
    # Web UI
    path('', ProductDashboardView.as_view(), name='product_dashboard'),
    path('add/', ProductCreatePageView.as_view(), name='product_create'),
    path('edit/<int:pk>/', ProductUpdatePageView.as_view(), name='product_edit'),
    path('delete/<int:pk>/', ProductDeleteWebView.as_view(), name='product_delete'),

    # API Endpoints
    path('admin/', admin.site.urls),
    path('api/products/', include('products.urls')),
    
    # Health check for Consul
    path('health', health_check, name='health_check'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
