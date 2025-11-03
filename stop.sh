#!/bin/bash

# AdDesigner Hub Bot - Optimized Stop Script

echo "🛑 Stopping AdDesigner Hub Bot..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to stop a service
stop_service() {
    local service_name="$1"
    local pid_file="logs/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        if kill -0 "$pid" 2>/dev/null; then
            echo "🔄 Stopping ${service_name} (PID: $pid)..."
            kill "$pid"
            
            # Wait for process to stop gracefully
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 15 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}⚠️  Force killing ${service_name}...${NC}"
                kill -9 "$pid"
            fi
            
            echo -e "${GREEN}✅ ${service_name} stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  ${service_name} was not running${NC}"
        fi
        
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  ${service_name} PID file not found${NC}"
    fi
}

# Stop the optimized bot
stop_service "bot"

# Also kill any remaining processes running main.py
echo "🔍 Checking for remaining bot processes..."
if pgrep -f "python main.py" > /dev/null; then
    echo "Killing remaining main.py processes..."
    pkill -f "python main.py" 2>/dev/null || true
fi

# Clean up any orphaned python processes
pkill -f "python3 main.py" 2>/dev/null || true

echo -e "${GREEN}🎉 AdDesigner Hub Bot stopped successfully!${NC}"
echo ""
echo "📝 Logs preserved in logs/ directory"
echo "🚀 To start again: ./start.sh"
echo "🧪 To test optimizations: ./start.sh test"