@echo off
title Companion Tibia - Bot Discord
color 0A

echo ==========================================
echo   COMPANION TIBIA - Rubinot Open PvP
echo   Por Soneca e Shawnks
echo ==========================================
echo.

:loop
echo [%TIME%] Iniciando bot...
python bot.py

echo.
echo [%TIME%] Bot encerrou. Reiniciando em 5 segundos...
echo   (Pressione Ctrl+C para parar definitivamente)
timeout /t 5 /nobreak >nul

goto loop
