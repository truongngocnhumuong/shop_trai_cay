# Frontend Web Service (Port 8000)

Service giao diện web cho hệ thống Fruit Shop SOA. Service này không sử dụng database riêng, chỉ gọi API từ các service khác.

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

2. Chạy migrations (để tạo database cho sessions):
```bash
python manage.py migrate
```

3. Thu thập static files (tùy chọn):
```bash
python manage.py collectstatic --noinput
```

## Chạy Service

Chạy service trên port 8000:
```bash
python manage.py runserver 8000
```

Hoặc sử dụng script:
```bash
run_server.bat
```

## Chức năng

### 1. Đăng nhập
- **URL:** `/login/`
- Gọi API từ Auth Service (Port 8001)
- Lưu token và thông tin user trong session
- Redirect đến trang danh sách sản phẩm sau khi đăng nhập thành công

### 2. Xem danh sách trái cây
- **URL:** `/products/`
- Gọi API từ Product Service (Port 8002) để lấy danh sách sản phẩm
- Gọi API từ Inventory Service (Port 8004) để hiển thị số lượng tồn kho
- Hiển thị sản phẩm dạng card với hình ảnh, giá, danh mục

### 3. Tạo đơn hàng
- **URL:** `/orders/create/`
- Form chọn sản phẩm và số lượng
- Gọi API từ Order Service (Port 8003) để tạo đơn hàng
- Hiển thị thông báo thành công/thất bại

## Tích hợp SOA

Service này giao tiếp với các service khác:

- **Auth Service (Port 8001)**: Đăng nhập, xác thực token
- **Product Service (Port 8002)**: Lấy danh sách sản phẩm
- **Order Service (Port 8003)**: Tạo đơn hàng
- **Inventory Service (Port 8004)**: Kiểm tra tồn kho (optional)

## Cấu trúc

```
frontend_service/
├── frontend_service/      # Django project settings
├── webapp/                # Main application
│   ├── templates/         # HTML templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── product_list.html
│   │   └── create_order.html
│   ├── static/            # Static files
│   │   └── css/
│   │       └── style.css
│   ├── utils.py           # API communication functions
│   ├── views.py           # View handlers
│   └── urls.py            # URL routing
└── manage.py
```

## Sử dụng

1. **Khởi động các service:**
   - Auth Service: Port 8001
   - Product Service: Port 8002
   - Order Service: Port 8003
   - Inventory Service: Port 8004 (optional)

2. **Khởi động Frontend Service:**
   ```bash
   python manage.py runserver 8000
   ```

3. **Truy cập:**
   - Mở trình duyệt: `http://127.0.0.1:8000/`
   - Đăng nhập với tài khoản từ Auth Service
   - Xem danh sách sản phẩm
   - Tạo đơn hàng

## Giao diện

- Sử dụng Bootstrap 5 cho responsive design
- Bootstrap Icons cho icons
- Custom CSS với gradient colors
- Modern card-based layout
- Responsive cho mobile và desktop

## Lưu ý

- Service chỉ sử dụng SQLite database để lưu sessions (không có models riêng)
- Tất cả dữ liệu nghiệp vụ được lấy từ các service khác qua API
- Session được sử dụng để lưu token và thông tin user
- Cần đảm bảo các service khác đang chạy trước khi sử dụng Frontend Service

