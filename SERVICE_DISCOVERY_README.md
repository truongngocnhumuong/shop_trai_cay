# Fruit Shop SOA - Service Discovery Integration

## Tổng Quan

Project đã được tích hợp **Consul Service Discovery** để cải thiện khả năng phát hiện dịch vụ, health monitoring và dynamic configuration.

## Các Thay Đổi Chính

### 1. Infrastructure
- ✅ **Docker Compose** cho Consul server
- ✅ **Common utilities** (`common/consul_client.py`) cho service registration/discovery
- ✅ **Health check endpoints** cho tất cả services (`/health`)

### 2. Service Registration
- ✅ Mỗi service tự động đăng ký với Consul khi khởi động
- ✅ Tự động hủy đăng ký khi service tắt
- ✅ Health checks mỗi 10 giây

### 3. Service Discovery
- ✅ Services sử dụng Consul để tìm nhau thay vì hardcoded URLs
- ✅ **Graceful fallback** về hardcoded URLs nếu Consul không khả dụng
- ✅ **Backward compatible** - hoạt động với/không có Consul

## Cài Đặt

### 1. Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

Dependencies mới:
- `python-consul>=1.1.0`

### 2. Khởi Động Consul Server

```bash
# Sử dụng Docker Compose
docker-compose up -d consul

# Kiểm tra Consul UI
# Mở browser: http://localhost:8500/ui
```

## Sử Dụng

### Chế Độ 1: Với Consul (Khuyến Nghị)

```bash
# Bật Consul cho tất cả services
set USE_CONSUL=true

# Khởi động các services
python auth_service/manage.py runserver 8001
python product_service/manage.py runserver 8002
python order_service/manage.py runserver 8003
python inventory_service/manage.py runserver 8004
```

**Lợi ích:**
- ✅ Dynamic service discovery
- ✅ Health monitoring tự động
- ✅ Failover support
- ✅ Dễ scale (multiple instances)

### Chế Độ 2: Không Dùng Consul (Backward Compatible)

```bash
# Tắt Consul (mặc định)
set USE_CONSUL=false

# Hoặc không set gì cả
# Khởi động services như bình thường
python auth_service/manage.py runserver 8001
python product_service/manage.py runserver 8002
python order_service/manage.py runserver 8003
python inventory_service/manage.py runserver 8004
```

**Hoạt động:**
- ✅ Sử dụng hardcoded URLs như cũ
- ✅ Không cần Consul server
- ✅ 100% tương thích với code cũ

## Kiểm Tra

### 1. Kiểm Tra Health Endpoints

```bash
# Auth Service
curl http://localhost:8001/health

# Product Service
curl http://localhost:8002/health

# Order Service
curl http://localhost:8003/health

# Inventory Service
curl http://localhost:8004/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "auth-service",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "user_model": "ok"
  }
}
```

### 2. Kiểm Tra Consul Registration

1. Mở Consul UI: http://localhost:8500/ui/dc1/services
2. Xác nhận thấy 4 services:
   - `auth-service`
   - `product-service`
   - `order-service`
   - `inventory-service`
3. Tất cả đều có status **"passing"** (màu xanh)

### 3. Test Service Discovery

```bash
# Tạo order mới - Order Service sẽ discover Product/Auth/Inventory services qua Consul
curl -X POST http://localhost:8003/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "items": [{"product_id": 1, "quantity": 2}]
  }'
```

**Logs sẽ hiển thị:**
```
Discovered product-service via Consul: http://localhost:8002
Discovered inventory-service via Consul: http://localhost:8004
```

### 4. Test Failover

```bash
# 1. Stop Product Service (Ctrl+C)

# 2. Kiểm tra Consul UI - product-service sẽ chuyển sang "critical" (màu đỏ)

# 3. Thử tạo order - sẽ fallback về hardcoded URL
# Logs sẽ hiển thị:
# "Consul discovery failed for product-service, using fallback"
# "Using fallback URL for product-service: http://localhost:8002"
```

## Environment Variables

| Variable | Default | Mô tả |
|----------|---------|-------|
| `USE_CONSUL` | `false` | Bật/tắt Consul integration |
| `CONSUL_HOST` | `localhost` | Consul server host |
| `CONSUL_PORT` | `8500` | Consul server port |
| `SERVICE_ADDRESS` | `localhost` | Địa chỉ service đăng ký với Consul |
| `PRODUCT_SERVICE_URL` | `http://localhost:8002` | Fallback URL cho Product Service |
| `AUTH_SERVICE_URL` | `http://localhost:8001` | Fallback URL cho Auth Service |
| `INVENTORY_SERVICE_URL` | `http://localhost:8004` | Fallback URL cho Inventory Service |

## Kiến Trúc

```
┌─────────────────┐
│  Consul Server  │
│   Port: 8500    │
└────────┬────────┘
         │
         │ Registration & Discovery
         │
    ┌────┴────┬────────┬────────┬────────┐
    │         │        │        │        │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼────┐ ┌──▼────┐
│ Auth  │ │Product│ │Order │ │Inventory│ │Frontend│
│ :8001 │ │ :8002 │ │ :8003│ │ :8004  │ │ :8000  │
└───────┘ └───────┘ └──────┘ └────────┘ └────────┘
```

## Troubleshooting

### Consul không khởi động

```bash
# Kiểm tra Docker
docker ps

# Xem logs
docker logs consul-server

# Restart
docker-compose restart consul
```

### Service không đăng ký với Consul

**Nguyên nhân:**
1. `USE_CONSUL=false` (mặc định)
2. Consul server chưa chạy
3. Lỗi network

**Giải pháp:**
```bash
# 1. Bật Consul
set USE_CONSUL=true

# 2. Kiểm tra Consul server
curl http://localhost:8500/v1/agent/self

# 3. Xem logs của service
# Sẽ thấy: "✓ [Service] registered with Consul"
```

### Service discovery không hoạt động

**Kiểm tra:**
1. Consul server có chạy không?
2. `USE_CONSUL=true` chưa?
3. Services đã đăng ký chưa? (xem Consul UI)

**Fallback:**
- Nếu Consul fail, system tự động dùng hardcoded URLs
- Không ảnh hưởng đến hoạt động của application

## Best Practices

### Development
```bash
# Có thể tắt Consul để dev nhanh hơn
set USE_CONSUL=false
```

### Production
```bash
# Nên bật Consul
set USE_CONSUL=true

# Set service address đúng (không phải localhost)
set SERVICE_ADDRESS=10.0.1.5
```

### Testing
```bash
# Test với Consul
set USE_CONSUL=true

# Test failover
# Stop một service và xem logs
```

## Migration từ Code Cũ

**Không cần thay đổi gì!**

Code cũ vẫn hoạt động 100% vì:
1. `USE_CONSUL=false` mặc định
2. Fallback mechanism tự động
3. Backward compatible

Để bật Consul, chỉ cần:
```bash
set USE_CONSUL=true
```

## Tóm Tắt

✅ **An toàn**: Backward compatible, có fallback mechanism  
✅ **Dễ dùng**: Chỉ cần set `USE_CONSUL=true`  
✅ **Production-ready**: Health checks, failover, scalability  
✅ **Không breaking changes**: Code cũ vẫn hoạt động  

---

**Lưu ý**: Đây là implementation an toàn, có thể rollback bất cứ lúc nào bằng cách set `USE_CONSUL=false`.
