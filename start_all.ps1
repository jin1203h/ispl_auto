# ISPL 시스템 통합 시작 스크립트
Write-Host "ISPL 시스템 시작 중..." -ForegroundColor Cyan
Write-Host ""

# 백엔드 서버 시작
Write-Host "1. 백엔드 서버 시작..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'D:\APP\ispl_auto\backend'; python main.py"

# 3초 대기
Write-Host "2. 3초 대기..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 프론트엔드 서버 시작
Write-Host "3. 프론트엔드 서버 시작..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'D:\APP\ispl_auto\frontend'; npm start"

Write-Host ""
Write-Host "✅ 모든 서버가 시작되었습니다!" -ForegroundColor Green
Write-Host "백엔드: http://localhost:8000" -ForegroundColor Blue
Write-Host "프론트엔드: http://localhost:3000" -ForegroundColor Blue
Write-Host ""
Write-Host "아무 키나 누르면 종료됩니다..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

