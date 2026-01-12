import time
from urllib.parse import urlencode
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import requests
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.sessions.models import Session
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .utils import (
    call_auth_service_login,
    call_auth_service_verify_token,
    get_products,
    get_all_inventories,
    create_order,
    create_payment,
    complete_payment_service
)

# Health check endpoint for Consul
def health_check(request):
    return JsonResponse({
        "status": "healthy",
        "service": "frontend-service",
        "version": "1.0.0"
    })

def index(request):
    """Home page - redirect to login or products"""
    if 'access_token' in request.session:
        return redirect('product_list')
    return redirect('login')

@csrf_exempt
@require_http_methods(["GET", "POST"])
def login_view(request):
    """Login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin đăng nhập.')
            return render(request, 'login.html')
        
        # Call Auth Service
        result = call_auth_service_login(username, password)
        
        if result['success']:
            # Store token and user info in session
            data = result['data']
            request.session['access_token'] = data.get('access')
            request.session['refresh_token'] = data.get('refresh')
            request.session['user_id'] = data.get('user', {}).get('id')
            request.session['username'] = data.get('user', {}).get('username')
            request.session['user_role'] = data.get('user', {}).get('role', 'customer')
            messages.success(request, f'Đăng nhập thành công! Chào mừng {username}')
            return redirect('product_list')
        else:
            messages.error(request, result.get('error', 'Đăng nhập thất bại. Vui lòng thử lại.'))
    
    return render(request, 'login.html')

def logout_view(request):
    """Logout and clear session"""
    request.session.flush()
    messages.success(request, 'Đã đăng xuất thành công.')
    return redirect('login')

@require_http_methods(["GET"])
def product_list_view(request):
    """Display list of products"""
    # Check if user is logged in
    if 'access_token' not in request.session:
        messages.warning(request, 'Vui lòng đăng nhập để xem sản phẩm.')
        return redirect('login')
    
    # Clear cache if requested
    if request.GET.get('clear_cache') == 'true':
        # Clear any existing cache
        if 'products_cache' in request.session:
            del request.session['products_cache']
        
        # Force a redirect to ensure a fresh request
        return redirect(reverse('product_list'))
    
    # Always fetch fresh products from the service
    result = get_products()
    
    if not result['success']:
        messages.error(request, result.get('error', 'Không thể tải danh sách sản phẩm.'))
        products = []
    else:
        products = result['data']
        
        # Get all inventories in one bulk request (OPTIMIZATION: Fix N+1 problem)
        inventory_data = get_all_inventories()
        inventory_map = {}
        if inventory_data['success']:
            # Create a map of product_id -> quantity for O(1) lookup
            for item in inventory_data['data']:
                inventory_map[item.get('product_id')] = item.get('quantity', 0)
        
        # Merge inventory data into products
        for product in products:
            product_id = product.get('id') or product.get('product_id')
            product['inventory_quantity'] = inventory_map.get(product_id, 0)
    
    context = {
        'products': products,
        'username': request.session.get('username', 'User'),
        'user_id': request.session.get('user_id'),
    }
    
    return render(request, 'product_list.html', context)

@require_http_methods(["GET", "POST"])
def create_order_view(request):
    """Create order page"""
    # Check if user is logged in
    if 'access_token' not in request.session:
        messages.warning(request, 'Vui lòng đăng nhập để tạo đơn hàng.')
        return redirect('login')
    
    user_id = request.session.get('user_id')
    
    if request.method == 'POST':
        # Get selected products from form
        items = []
        product_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')
        
        for product_id, quantity in zip(product_ids, quantities):
            if product_id and quantity and int(quantity) > 0:
                items.append({
                    'product_id': int(product_id),
                    'quantity': int(quantity)
                })
        
        if not items:
            messages.error(request, 'Vui lòng chọn ít nhất một sản phẩm.')
            # Reload products for the form
            result = get_products()
            products = result.get('data', []) if result['success'] else []
            
            # Get all inventories in one bulk request (OPTIMIZATION: Fix N+1 problem)
            inventory_data = get_all_inventories()
            inventory_map = {}
            if inventory_data['success']:
                for item in inventory_data['data']:
                    inventory_map[item.get('product_id')] = item.get('quantity', 0)
            
            # Merge inventory data into products
            for product in products:
                product_id = product.get('id') or product.get('product_id')
                product['inventory_quantity'] = inventory_map.get(product_id, 0)
            
            context = {
                'products': products,
                'username': request.session.get('username', 'User'),
            }
            return render(request, 'create_order.html', context)
        
        # Create order via Order Service
        access_token = request.session.get('access_token')
        result = create_order(user_id, items, access_token)
        
        if result['success']:
            # Initialize payment
            order_data = result['data']
            payment_result = create_payment(order_data.get("id"), order_data.get("total_price"))
            if payment_result['success']:
                payment_id = payment_result['data'].get('id')
                # Redirect to the new Checkout UI via Gateway
                gateway_url = getattr(settings, 'GATEWAY_URL', 'http://localhost:8005')
                return redirect(f"{gateway_url}/checkout/{payment_id}/")
            
            error_msg = payment_result.get('error', 'Lỗi không xác định')
            messages.error(request, f'Đơn hàng #{order_data.get("id")} đã được tạo, nhưng không thể khởi tạo thanh toán: {error_msg}')
            return redirect('product_list')
        else:
            messages.error(request, result.get('error', 'Không thể tạo đơn hàng. Vui lòng thử lại.'))
    
    # GET request - show form
    result = get_products()
    products = result.get('data', []) if result['success'] else []
    
    # Get all inventories in one bulk request (OPTIMIZATION: Fix N+1 problem)
    inventory_data = get_all_inventories()
    inventory_map = {}
    if inventory_data['success']:
        for item in inventory_data['data']:
            inventory_map[item.get('product_id')] = item.get('quantity', 0)
    
    # Merge inventory data into products
    for product in products:
        product_id = product.get('id') or product.get('product_id')
        product['inventory_quantity'] = inventory_map.get(product_id, 0)
    
    context = {
        'products': products,
        'username': request.session.get('username', 'User'),
    }
    
    return render(request, 'create_order.html', context)

@require_http_methods(["GET", "POST"])
def payment_view(request, payment_id):
    """Payment page"""
    if 'access_token' not in request.session:
        return redirect('login')
        
    if request.method == 'POST':
        result = complete_payment_service(payment_id)
        if result['success']:
            messages.success(request, 'Thanh toán thành công! Đơn hàng của bạn đã được hoàn tất.')
            return render(request, 'payment_success.html', {'data': result['data']})
        else:
            messages.error(request, f"Lỗi thanh toán: {result.get('error')}")
            
    # GET request - fetch payment details (we can add a get_payment util if needed, but for now we'll just show the button)
    return render(request, 'payment.html', {'payment_id': payment_id})

