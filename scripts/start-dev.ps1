# ==============================================================================
# FraudLens Development Stack Launcher (PowerShell)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  FraudLens — AI Fraud-Ring Intelligence for Razorpay     " -ForegroundColor Green
Write-Host "  'See the fraud behind the transaction.'                 " -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start Infrastructure (if Docker is running)
if (Get-Process -Name "*docker*" -ErrorAction SilentlyContinue) {
    Write-Host "[+] Starting PostgreSQL & Neo4j via Docker Compose..." -ForegroundColor Yellow
    docker compose -f infra/docker-compose.yml up -d
} else {
    Write-Host "[i] Note: Start Docker Desktop to launch PostgreSQL & Neo4j containers." -ForegroundColor DarkGray
}

# 2. Launch FastAPI in new terminal
Write-Host "[+] Launching FastAPI Gateway on http://localhost:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn app.main:app --app-dir apps/api --reload --port 8000"

# 3. Launch Next.js in new terminal
Write-Host "[+] Launching Next.js Command Center on http://localhost:3000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/web; npm run dev"

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  FraudLens Stack Initialized!                            " -ForegroundColor Green
Write-Host "  - Command Center: http://localhost:3000                 " -ForegroundColor White
Write-Host "  - API Liveness:   http://localhost:8000/health          " -ForegroundColor White
Write-Host "  - Deep Health:    http://localhost:8000/api/v1/health   " -ForegroundColor White
Write-Host "  - Swagger Docs:   http://localhost:8000/docs            " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
