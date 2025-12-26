# Inventory Service (Port 8004)

Service quản lý tồn kho sản phẩm cho hệ thống Fruit Shop SOA.

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

Chạy service trên port 8004:
```bash
python manage.py runserver 8004
```

Hoặc sử dụng script:
```bash
run_server.bat
```

## API Endpoints

### GET /api/inventory/
Lấy danh sách tất cả inventory records

**Response:**
```json
[
  {
    "id": 1,
    "product_id": 1,
    "product_info": {
      "id": 1,
      "name": "Apple",
      "category": "other",
      "price": "25.50"
    },
    "quantity": 100,
    "created_at": "2025-12-26T12:00:00Z",
    "updated_at": "2025-12-26T12:00:00Z"
  }
]
```

### GET /api/inventory/{product_id}/
Lấy thông tin tồn kho của một sản phẩm cụ thể

**Response:**
```json
{
  "id": 1,
  "product_id": 1,
  "product_info": {
    "id": 1,
    "name": "Apple",
    "category": "other",
    "price": "25.50"
  },
  "quantity": 100,
  "created_at": "2025-12-26T12:00:00Z",
  "updated_at": "2025-12-26T12:00:00Z"
}
```

**Note:** Nếu inventory record chưa tồn tại, sẽ tự động tạo với quantity = 0.

### PUT /api/inventory/update/
Cập nhật số lượng tồn kho

#### Single Update (Cập nhật một sản phẩm):
**Request Body:**
```json
{
  "product_id": 1,
  "quantity": 100
}
```

#### Bulk Update (Cập nhật nhiều sản phẩm):
**Request Body:**
```json
{
  "updates": [
    {"product_id": 1, "quantity": 100},
    {"product_id": 2, "quantity": 50},
    {"product_id": 3, "quantity": 75}
  ]
}
```

**Response (Bulk Update):**
```json
{
  "success": true,
  "updated": 3,
  "results": [
    {"product_id": 1, "quantity": 100, "status": "success"},
    {"product_id": 2, "quantity": 50, "status": "success"},
    {"product_id": 3, "quantity": 75, "status": "success"}
  ],
  "errors": []
}
```

## Model

**Inventory:**
- `product_id`: IntegerField (unique)
- `quantity`: PositiveIntegerField (default=0, min_value=0)
- `created_at`: DateTimeField (auto_now_add)
- `updated_at`: DateTimeField (auto_now)

**Methods:**
- `decrease(amount)`: Giảm số lượng tồn kho
- `increase(amount)`: Tăng số lượng tồn kho
- `set_quantity(quantity)`: Đặt số lượng tồn kho

## Tích hợp SOA

Service này giao tiếp với:
- **Product Service (Port 8002)**: Validate product_id và lấy thông tin sản phẩm
- **Order Service (Port 8003)**: Có thể được gọi để cập nhật inventory sau khi tạo đơn hàng

**Lưu ý:** Service không JOIN database với Product Service, tất cả thông tin sản phẩm được lấy qua API calls.

## Sử dụng với Order Service

Khi Order Service tạo đơn hàng, có thể gọi Inventory Service để cập nhật tồn kho:

```python
# Trong Order Service, sau khi tạo order thành công
import requests

order_data = {
    'items': [
        {'product_id': 1, 'quantity': 2},
        {'product_id': 2, 'quantity': 3}
    ]
}

# Gọi Inventory Service để giảm tồn kho
response = requests.put(
    'http://localhost:8004/api/inventory/update/',
    json={'updates': [
        {'product_id': item['product_id'], 'quantity': current_qty - item['quantity']}
        for item in order_data['items']
    ]}
)
```

## Ví dụ sử dụng

### 1. Khởi tạo tồn kho cho sản phẩm
```bash
PUT http://127.0.0.1:8004/api/inventory/update/
{
  "product_id": 1,
  "quantity": 100
}
```

### 2. Kiểm tra tồn kho
```bash
GET http://127.0.0.1:8004/api/inventory/1/
```

### 3. Cập nhật hàng loạt
```bash
PUT http://127.0.0.1:8004/api/inventory/update/
{
  "updates": [
    {"product_id": 1, "quantity": 95},
    {"product_id": 2, "quantity": 80}
  ]
}
```

