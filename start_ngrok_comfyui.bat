@echo off
title NarrAI - Ngrok ComfyUI Tunnel
color 0B
echo ========================================================
echo    NarrAI: Mo Duong Ham Ngrok Cho ComfyUI (Port 8188)
echo ========================================================
echo.
echo [1] Kiem tra ComfyUI dang chay o cong 8188...
netstat -ano | findstr ":8188" >nul
if %errorlevel% neq 0 (
    echo [CANH BAO] Khong thay ComfyUI chay o cong 8188!
    echo Hay bat ComfyUI truoc khi chay script nay.
    echo.
) else (
    echo [OK] ComfyUI dang hoat dong o cong 8188.
)

echo.
echo [2] Dang khoi dong ngrok http 8188...
echo Hay copy duong link https://xxxx.ngrok-free.app duoc tao ra ben duoi!
echo.
ngrok http 8188
pause
