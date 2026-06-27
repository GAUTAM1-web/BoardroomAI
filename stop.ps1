Write-Host ""
Write-Host "Stopping Boardroom AI..." -ForegroundColor Yellow

Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host ""
Write-Host "Boardroom AI stopped." -ForegroundColor Green