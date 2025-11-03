#!/bin/bash

# AdDesigner Hub Bot - Optimized Production Start Script
# Updated for simplified 8-file architecture with performance optimizations

set -e

# Quick start mode - optimized for current structure
if [ "$1" = "quick" ]; then
    echo "🚀 Quick start mode..."
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    nohup python src/main.py > logs/bot.log 2>&1 &
    echo $! > logs/bot.pid
    echo "✅ Bot started in background (PID: $!)"
    echo "📝 Check logs: tail -f logs/bot.log"
    exit 0
fi

# Test mode - run optimization verification
if [ "$1" = "test" ]; then
    echo "🧪 Testing optimizations..."
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    echo "Running database optimization tests..."
    python test_database_optimization.py
    echo ""
    echo "Running basic import tests..."
    python -c "
try:
    print('✅ Testing imports...')
    import sys
    sys.path.insert(0, 'src')
    from src.database import DatabaseManager, db_manager
    print('✅ DatabaseManager imported')
    from src.handlers import router
    print('✅ Handlers imported')
    from src.services import ai_service
    print('✅ Services imported')
    from src.utils import MessageLoader
    print('✅ Utils imported')
    from src.config import settings
    print('✅ Config imported')
    print('🎉 All optimized modules working!')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
"
    exit 0
fi

# Debug mode - enhanced with optimization info
if [ "$1" = "debug" ]; then
    echo "🐛 Debug mode with optimization info..."
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    echo "Testing basic imports and optimizations..."
    python -c "
try:
    print('✅ Python works')
    import sys
    sys.path.insert(0, 'src')
    print(f'✅ Python path: {sys.path[0]}')
    from dotenv import load_dotenv
    load_dotenv()
    print('✅ dotenv works')
    from src.config import settings
    print('✅ Config works')
    print(f'Bot token length: {len(settings.telegram_bot_token)}')
    
    # Test DatabaseManager optimization
    from src.database import DatabaseManager, db_manager
    print('✅ DatabaseManager Singleton works')
    print(f'Engine type: {type(db_manager._engine).__name__ if db_manager._engine else \"Not initialized\"}')
    
    # Test file structure
    import os
    files = ['src/handlers.py', 'src/database.py', 'src/services.py', 'src/utils.py', 'src/config.py', 'src/main.py']
    for f in files:
        if os.path.exists(f):
            size = os.path.getsize(f) // 1024
            print(f'✅ {f}: {size}KB')
        else:
            print(f'❌ Missing: {f}')
            
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
"
    exit 0
fi

echo "🚀 Starting AdDesigner Hub Bot..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Please create .env file with required configuration."
    exit 1
fi

# Source environment variables
source .env

# Check required environment variables - simplified list
check_env_var() {
    if [ -z "${!1}" ]; then
        echo -e "${RED}❌ Error: $1 environment variable is not set!${NC}"
        return 1
    fi
}

echo "🔍 Checking environment variables..."
check_env_var "TELEGRAM_BOT_TOKEN"

# Optional checks with warnings - updated for current features
if [ -z "$ADMIN_ID" ]; then
    echo -e "${YELLOW}⚠️  Warning: ADMIN_ID not set. Admin features will be disabled.${NC}"
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Warning: OPENAI_API_KEY not set. AI features will be disabled.${NC}"
fi

if [ -z "$YOOKASSA_SHOP_ID" ] && [ -z "$STRIPE_SECRET_KEY" ] && [ -z "$NOWPAYMENTS_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Warning: No payment providers configured. Payment features will be disabled.${NC}"
fi

# Create directories - minimal set for current architecture
echo "📁 Creating required directories..."
mkdir -p logs

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔗 Activating virtual environment..."
export PATH="$(pwd)/venv/bin:$PATH"

# Install/upgrade dependencies - optimized for simplified structure
echo "📦 Installing dependencies..."
if [ ! -f ".dependencies_installed" ]; then
    ./venv/bin/pip install --upgrade pip --quiet
    
    # Install core dependencies for optimized bot
    echo "Installing core dependencies..."
    ./venv/bin/pip install --quiet \
        aiogram==3.13.1 \
        pydantic-settings \
        SQLAlchemy \
        aiosqlite \
        python-dotenv \
        openai \
        aiohttp \
        pillow
    
    # Try to install requirements.txt if exists
    if [ -f "requirements.txt" ]; then
        ./venv/bin/pip install -r requirements.txt --quiet || echo "⚠️ Some optional dependencies failed to install"
    fi
    
    touch .dependencies_installed
    echo "✅ Dependencies installed for optimized architecture"
else
    echo "✅ Dependencies already installed (remove .dependencies_installed to reinstall)"
fi

# Initialize database with optimized DatabaseManager
echo "🗄️  Initializing database with optimizations..."
./venv/bin/python -c "
import sys
sys.path.insert(0, 'src')
try:
    from src.database import db_manager
    print('✅ DatabaseManager Singleton initialized')
    
    # Initialize database with optimizations
    db_manager.init_db()
    print('✅ Database tables created with connection pooling')
    
    # Test optimization
    with db_manager.get_session() as session:
        print('✅ Session context manager working')
        
    print('🚀 Database ready with performance optimizations')
except Exception as e:
    print(f'❌ Database initialization error: {e}')
    import traceback
    traceback.print_exc()
"

# Function to start the optimized bot
start_bot() {
    echo "🤖 Starting optimized bot..."
    
    # Check if bot is already running
    if pgrep -f "python src/main.py" > /dev/null; then
        echo -e "${YELLOW}⚠️  Bot is already running${NC}"
        return 0
    fi
    
    # Start bot in background with optimizations
    nohup ./venv/bin/python src/main.py > logs/bot.log 2>&1 &
    local pid=$!
    
    # Wait a moment and check if process is still running
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ Optimized bot started successfully (PID: $pid)${NC}"
        echo "$pid" > logs/bot.pid
        
        # Show optimization status
        echo "🚀 Active optimizations:"
        echo "  • DatabaseManager Singleton pattern"
        echo "  • Connection pooling (size=10, overflow=20)"
        echo "  • Automatic session cleanup"
        echo "  • Single-channel architecture"
        return 0
    else
        echo -e "${RED}❌ Failed to start bot${NC}"
        echo "Last few lines of log:"
        tail -10 logs/bot.log
        return 1
    fi
}

# Start services based on mode - simplified for current architecture
if [ "$1" = "bot" ] || [ "$1" = "" ]; then
    echo "🚀 Starting optimized AdDesigner Hub Bot..."
    start_bot
else
    echo "Usage: $0 [bot|test|debug|quick]"
    echo "  bot     - Start the optimized Telegram bot (default)"
    echo "  test    - Run optimization tests"
    echo "  debug   - Debug mode with optimization info"
    echo "  quick   - Quick start in background"
    echo ""
    echo "🔧 Available optimizations:"
    echo "  • DatabaseManager Singleton pattern"
    echo "  • Connection pooling for better performance"
    echo "  • Simplified 8-file architecture"
    echo "  • Single-channel mode for focused operation"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 AdDesigner Hub Bot started successfully with optimizations!${NC}"
echo ""
echo "📊 Service Status:"
if [ -f "logs/bot.pid" ]; then
    echo "  🤖 Optimized Bot: Running (PID: $(cat logs/bot.pid))"
fi
echo ""
echo "📝 Monitoring:"
echo "  📋 Bot logs: tail -f logs/bot.log"
echo "  🧪 Test optimizations: ./start.sh test"
echo "  🐛 Debug mode: ./start.sh debug"
echo ""
echo "� Performance Features Active:"
echo "  • DatabaseManager Singleton pattern"
echo "  • Connection pooling (10 base + 20 overflow)"
echo "  • Automatic session management"
echo "  • Simplified 8-file architecture"
echo ""
echo "🛑 To stop: pkill -f 'python src/main.py' || kill \$(cat logs/bot.pid)"