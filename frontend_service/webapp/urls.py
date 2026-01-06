from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('health', views.health_check, name='health_check'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('products/', views.product_list_view, name='product_list'),
    path('orders/create/', views.create_order_view, name='create_order'),
]
