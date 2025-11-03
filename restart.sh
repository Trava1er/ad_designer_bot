#!/bin/bash

# Restart script for AdDesigner Bot
# Usage: ./restart.sh

echo "🔄 Перезапуск бота..."

# Stop the bot
./stop.sh

# Wait for processes to fully terminate
echo "⏳ Ожидание завершения процессов..."
sleep 3

# Double check - kill any remaining processes
pkill -9 -f "python.*main.py" 2>/dev/null || true
pkill -9 -f "python3.*main.py" 2>/dev/null || true

# Wait a bit more
sleep 2

# Start the bot
./start.sh

echo "✅ Бот перезапущен!"
