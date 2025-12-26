# Product Service (Port 8002)

Service quản lý sản phẩm trái cây cho hệ thống Fruit Shop SOA.

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

Chạy service trên port 8002:
```bash
python manage.py runserver 8002
```

Hoặc sử dụng script:
```bash
run_server.bat
```

## API Endpoints

### GET /api/products/
Lấy danh sách tất cả sản phẩm

**Response:**
```json
[
  {
    "id": 1,
    "name": "Apple",
    "price": "25.50",
    "category": "other",
    "image": null,
    "image_url": null,
    "created_at": "2025-12-26T11:00:00Z",
    "updated_at": "2025-12-26T11:00:00Z"
  }
]
```

### POST /api/products/
Tạo sản phẩm mới

**Request Body:**
```json
{
  "name": "Apple",
  "price": "25.50",
  "category": "other",
  "image": "<file>"
}
```

**Categories:** tropical, citrus, berries, stone, melons, other

### PUT /api/products/{id}/
Cập nhật sản phẩm

**Request Body:**
```json
{
  "name": "Red Apple",
  "price": "30.00",
  "category": "other",
  "image": "<file>"
}
```

### DELETE /api/products/{id}/
Xóa sản phẩm

**Response:** 204 No Content

## Model

**Product:**
- `name`: CharField (max_length=200)
- `price`: DecimalField (max_digits=10, decimal_places=2)
- `category`: CharField (choices: tropical, citrus, berries, stone, melons, other)
- `image`: ImageField (upload_to='products/')
- `created_at`: DateTimeField (auto_now_add)
- `updated_at`: DateTimeField (auto_now)

