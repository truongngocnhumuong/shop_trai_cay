import time
from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.sessions.models import Session
from django.urls import reverse

from .utils import (
    call_auth_service_login,
    call_auth_service_verify_token,
    get_products,
    get_inventory,
    create_order
)

def index(request):
    """Home page - redirect to login or products"""
    if 'access_token' in request.session:
        return redirect('product_list')
    return redirect('login')

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
        
        # Get fresh inventory for each product
        for product in products:
            if not isinstance(product, dict):
                print(f"Warning: Product is not a dictionary: {product}")
                continue
                
            product_id = product.get('id') or product.get('product_id')
            if not product_id:
                print(f"Warning: Could not find ID in product: {product}")
                continue
                
            # Add a timestamp to ensure we don't get a cached response
            timestamp = int(time.time())
            inventory_result = get_inventory(product_id)
            
            if inventory_result['success']:
                product['inventory_quantity'] = inventory_result['data'].get('quantity', 0)
            else:
                product['inventory_quantity'] = None  # Unknown
    
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
            
            # Get inventory for each product
            for product in products:
                if not isinstance(product, dict):
                    continue
                    
                product_id = product.get('id') or product.get('product_id')
                if not product_id:
                    continue
                    
                inventory_result = get_inventory(product_id)
                
                if inventory_result['success']:
                    product['inventory_quantity'] = inventory_result['data'].get('quantity', 0)
                else:
                    product['inventory_quantity'] = None  # Unknown
            
            context = {
                'products': products,
                'username': request.session.get('username', 'User'),
            }
            return render(request, 'create_order.html', context)
        
        # Create order via Order Service
        access_token = request.session.get('access_token')
        result = create_order(user_id, items, access_token)
        
        if result['success']:
            order_data = result['data']
            messages.success(request, f'Đơn hàng #{order_data.get("id")} đã được tạo thành công!')
            
            # Clear any cached product data
            if 'products_cache' in request.session:
                del request.session['products_cache']
            
            # Force a redirect with a timestamp to ensure fresh data
            return redirect(f"{reverse('product_list')}?clear_cache=true&_={int(time.time())}")
        else:
            messages.error(request, result.get('error', 'Không thể tạo đơn hàng. Vui lòng thử lại.'))
    
    # GET request - show form
    result = get_products()
    products = result.get('data', []) if result['success'] else []
    
    # Get inventory for each product
    for product in products:
        if not isinstance(product, dict):
            continue
            
        product_id = product.get('id') or product.get('product_id')
        if not product_id:
            continue
            
        inventory_result = get_inventory(product_id)
        
        if inventory_result['success']:
            product['inventory_quantity'] = inventory_result['data'].get('quantity', 0)
        else:
            product['inventory_quantity'] = None  # Unknown
    
    context = {
        'products': products,
        'username': request.session.get('username', 'User'),
    }
    
    return render(request, 'create_order.html', context)

