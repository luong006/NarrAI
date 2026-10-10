@echo off
title ComfyUI Ngrok Tunnel for NarrAI
echo ===================================================
echo   NarrAI - ComfyUI Ngrok Tunnel Starter
echo ===================================================
echo.
echo Dang khoi dong Ngrok tren cong 8188 (ComfyUI Desktop)...
echo.
echo Hay sao chep duong link dang: https://xxxx.ngrok-free.app
echo va dan vao bien COMFYUI_URL trong backend/.env hoac tren Render!
echo.
ngrok http 8188
pause
