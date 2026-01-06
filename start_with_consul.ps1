# PowerShell script to start all services with Consul enabled

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Fruit Shop SOA with Consul" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variable globally for this session
$env:USE_CONSUL = "true"
$BASE_DIR = $PWD.Path
$VENV_PYTHON = "$BASE_DIR\venv\Scripts\python.exe"

Write-Host "[1/5] Starting Consul Server..." -ForegroundColor Yellow
docker-compose up -d consul
Start-Sleep -Seconds 3

Write-Host "[2/5] Starting Auth Service on port 8001..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BASE_DIR\auth_service'; `$env:USE_CONSUL='true'; & '$VENV_PYTHON' manage.py runserver 8001" -WindowStyle Normal
Start-Sleep -Seconds 2

Write-Host "[3/5] Starting Product Service on port 8002..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BASE_DIR\product_service'; `$env:USE_CONSUL='true'; & '$VENV_PYTHON' manage.py runserver 8002" -WindowStyle Normal
Start-Sleep -Seconds 2

Write-Host "[4/5] Starting Order Service on port 8003..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BASE_DIR\order_service'; `$env:USE_CONSUL='true'; & '$VENV_PYTHON' manage.py runserver 8003" -WindowStyle Normal
Start-Sleep -Seconds 2

Write-Host "[5/6] Starting Inventory Service on port 8004..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BASE_DIR\inventory_service'; `$env:USE_CONSUL='true'; & '$VENV_PYTHON' manage.py runserver 8004" -WindowStyle Normal
Start-Sleep -Seconds 2

Write-Host "[6/6] Starting Frontend Service on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BASE_DIR\frontend_service'; `$env:USE_CONSUL='true'; & '$VENV_PYTHON' manage.py runserver 8000" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All services started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Consul UI: http://localhost:8500/ui" -ForegroundColor Cyan
Write-Host "Frontend Service: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Auth Service: http://localhost:8001" -ForegroundColor Cyan
Write-Host "Product Service: http://localhost:8002" -ForegroundColor Cyan
Write-Host "Order Service: http://localhost:8003" -ForegroundColor Cyan
Write-Host "Inventory Service: http://localhost:8004" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to open Consul UI..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Start-Process "http://localhost:8500/ui"
