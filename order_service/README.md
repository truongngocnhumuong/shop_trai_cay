# Order Service (Port 8003)

Service quản lý đơn hàng cho hệ thống Fruit Shop SOA.

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

2. Chạy migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Tạo superuser (tùy chọn):
```bash
python manage.py createsuperuser
```

## Chạy Service

Chạy service trên port 8003:
```bash
python manage.py runserver 8003
```

Hoặc sử dụng script:
```bash
run_server.bat
```

## API Endpoints

### GET /api/orders/
Lấy danh sách tất cả đơn hàng

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "total_price": "50.00",
    "status": "pending",
    "order_items": [
      {
        "id": 1,
        "product_id": 1,
        "product_info": {
          "id": 1,
          "name": "Apple",
          "category": "other",
          "image_url": "http://localhost:8002/media/products/apple.jpg"
        },
        "quantity": 2,
        "price": "25.00",
        "subtotal": "50.00",
        "created_at": "2025-12-26T11:00:00Z"
      }
    ],
    "created_at": "2025-12-26T11:00:00Z",
    "updated_at": "2025-12-26T11:00:00Z"
  }
]
```

### POST /api/orders/
Tạo đơn hàng mới

**Request Body:**
```json
{
  "user_id": 1,
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    },
    {
      "product_id": 2,
      "quantity": 3
    }
  ]
}
```

**Response:** Order object với thông tin đầy đủ

### GET /api/orders/{id}/
Lấy thông tin chi tiết đơn hàng

### PUT /api/orders/{id}/
Cập nhật đơn hàng (chủ yếu là status)

**Request Body:**
```json
{
  "status": "completed"
}
```

**Status values:** pending, processing, completed, cancelled

### DELETE /api/orders/{id}/
Xóa đơn hàng

### GET /api/orders/{order_id}/items/
Lấy danh sách items trong đơn hàng

### GET /api/orders/{order_id}/items/{id}/
Lấy thông tin chi tiết một item

### PUT /api/orders/{order_id}/items/{id}/
Cập nhật order item (quantity)

**Request Body:**
```json
{
  "quantity": 5
}
```

### DELETE /api/orders/{order_id}/items/{id}/
Xóa order item

## Model

**Order:**
- `user_id`: IntegerField
- `total_price`: DecimalField (max_digits=10, decimal_places=2)
- `status`: CharField (choices: pending, processing, completed, cancelled)
- `created_at`: DateTimeField (auto_now_add)
- `updated_at`: DateTimeField (auto_now)

**OrderItem:**
- `order`: ForeignKey to Order
- `product_id`: IntegerField
- `quantity`: PositiveIntegerField
- `price`: DecimalField (lưu giá tại thời điểm đặt hàng)
- `created_at`: DateTimeField (auto_now_add)

## Tích hợp SOA

Service này giao tiếp với:
- **Product Service (Port 8002)**: Lấy thông tin sản phẩm qua API
- **Auth Service (Port 8001)**: Xác thực user (có thể mở rộng sau)

**Lưu ý:** Service không JOIN database với Product Service, tất cả thông tin sản phẩm được lấy qua API calls.

