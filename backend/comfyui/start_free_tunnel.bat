@echo off
title Tao Link Tunnel Moi Cho ComfyUI (NarrAI)
echo ===================================================
echo   NarrAI - Tao Link Tunnel Doc Lap Cho ComfyUI
echo ===================================================
echo.
echo 1. Chay bang Cloudflare Tunnel (Khong trung voi Ngrok, Khong can dang ky)
echo 2. Chay bang Localtunnel (Tao link moi qua npx)
echo 3. Chay bang Ngrok moi
echo.
set /p opt="Chon phuong an (1, 2 hoac 3): "

if "%opt%"=="1" (
    echo.
    echo Dang khoi dong Cloudflare Quick Tunnel cho cong 8188...
    echo Hay copy link co duoi: .trycloudflare.com
    cloudflared tunnel --url http://127.0.0.1:8188
)

if "%opt%"=="2" (
    echo.
    echo Dang khoi dong Localtunnel cho cong 8188...
    call npx localtunnel --port 8188
)

if "%opt%"=="3" (
    echo.
    echo Dang khoi dong Ngrok cho cong 8188...
    ngrok http 8188
)

pause
