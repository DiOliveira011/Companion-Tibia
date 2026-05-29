#!/bin/bash
# Companion Tibia — Auto-restart no Linux/Mac

echo "=========================================="
echo "  COMPANION TIBIA - Rubinot Open PvP"
echo "  Por Soneca e Shawnks"
echo "=========================================="

while true; do
    echo "[$(date '+%H:%M:%S')] Iniciando bot..."
    python3 bot.py
    echo "[$(date '+%H:%M:%S')] Bot encerrou. Reiniciando em 5s..."
    sleep 5
done
