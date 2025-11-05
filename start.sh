#!/bin/bash

# Скрипт запуска всего проекта (Backend + Frontend)
# Использование: ./start.sh
# 
# Внимание: Этот скрипт использует отдельные терминалы для каждого сервера
# Для macOS использует osascript, для Linux - gnome-terminal/xterm

echo "🚀 Запуск Creo Manager (Backend + Frontend)"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Определяем ОС и запускаем в отдельных терминалах
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "📦 Запуск Backend в новом терминале..."
    osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && ./start_backend.sh\""
    
    sleep 2
    
    echo "📦 Запуск Frontend в новом терминале..."
    osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && ./start_frontend.sh\""
    
    echo ""
    echo "✅ Оба сервера запущены в отдельных окнах терминала!"
    echo ""
    echo "   Backend:  http://localhost:8000"
    echo "   Frontend: http://localhost:3000"
    echo ""
    echo "   Закройте окна терминала для остановки серверов"
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v gnome-terminal &> /dev/null; then
        echo "📦 Запуск Backend..."
        gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && ./start_backend.sh; exec bash"
        
        sleep 2
        
        echo "📦 Запуск Frontend..."
        gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && ./start_frontend.sh; exec bash"
    elif command -v xterm &> /dev/null; then
        echo "📦 Запуск Backend..."
        xterm -e "cd '$SCRIPT_DIR' && ./start_backend.sh" &
        
        sleep 2
        
        echo "📦 Запуск Frontend..."
        xterm -e "cd '$SCRIPT_DIR' && ./start_frontend.sh" &
    else
        echo "⚠️  Не найдены подходящие терминалы (gnome-terminal или xterm)"
        echo "   Запустите серверы вручную в отдельных терминалах:"
        echo "   Терминал 1: ./start_backend.sh"
        echo "   Терминал 2: ./start_frontend.sh"
        exit 1
    fi
    
    echo ""
    echo "✅ Оба сервера запущены в отдельных окнах терминала!"
else
    echo "⚠️  Неподдерживаемая ОС. Запустите серверы вручную:"
    echo "   Терминал 1: ./start_backend.sh"
    echo "   Терминал 2: ./start_frontend.sh"
    exit 1
fi

