Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "      Starting Boardroom AI" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Project Root
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start Backend
Start-Process powershell -WindowStyle Minimized -ArgumentList @(
"-NoExit",
"-Command",
"cd '$root\backend'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
)

Write-Host "Backend starting..."

Start-Sleep -Seconds 4

# Start Frontend
Start-Process powershell -WindowStyle Minimized -ArgumentList @(
"-NoExit",
"-Command",
"cd '$root\frontend'; npm run dev"
)

Write-Host "Frontend starting..."

Start-Sleep -Seconds 6

Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "Boardroom AI is ready!" -ForegroundColor Green