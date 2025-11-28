#!/usr/bin/env bash
# ==============================================================================
# MLSDM Environment Initialization Script
# ==============================================================================
# This script initializes the MLSDM environment by loading configuration from
# mlsdm_config.sh in the project root.
#
# Usage:
#   source bin/mlsdm-env.sh
#   # or
#   ./bin/mlsdm-env.sh  (if you need to execute it directly)
#
# Features:
#   - Context-independent: works from any directory
#   - Defensive programming: validates config file thoroughly
#   - Cognitive feedback: clear error messages with instructions
# ==============================================================================

set -euo pipefail
IFS=$'\n\t'

# ==============================================================================
# 1. ВИЗНАЧЕННЯ ЯКІРНОЇ ТОЧКИ (CONTEXT RESOLUTION)
# ==============================================================================
# Визначаємо реальний шлях до скрипта, ігноруючи symlink'и та місце запуску
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Припускаємо архітектуру: скрипт в /bin, конфіг в корені проекту
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="mlsdm_config.sh"
CONFIG_PATH="$PROJECT_ROOT/$CONFIG_FILE"

# ==============================================================================
# 2. ВАЛІДАЦІЯ ТА ЗАВАНТАЖЕННЯ (DEFENSIVE LOADING)
# ==============================================================================

# Перевірка: файл існує AND файл читабельний
if [ -f "$CONFIG_PATH" ] && [ -r "$CONFIG_PATH" ]; then
    
    # Перевірка: файл не порожній
    if [ ! -s "$CONFIG_PATH" ]; then
        echo "⚠️  WARNING: Файл конфігурації знайдено, але він порожній: $CONFIG_PATH"
    fi

    # shellcheck source=/dev/null
    source "$CONFIG_PATH"
    echo "✅ SUCCESS: Завантажено конфігурацію: $CONFIG_PATH"

else
    # ==========================================================================
    # 3. ОБРОБКА ПОМИЛОК (COGNITIVE FEEDBACK)
    # ==========================================================================
    echo "🛑 CRITICAL ERROR: Неможливо ініціалізувати середовище MLSDM."
    echo "-------------------------------------------------------------"
    echo "🔍 Діагностика:"
    if [ ! -f "$CONFIG_PATH" ]; then
        echo "   [X] Файл не знайдено."
        echo "   -> Очікуваний шлях: $CONFIG_PATH"
        echo "   -> Дія: Скопіюйте 'mlsdm_config.example.sh' у 'mlsdm_config.sh'."
    elif [ ! -r "$CONFIG_PATH" ]; then
        echo "   [X] Відмовлено у доступі (Permission denied)."
        echo "   -> Шлях: $CONFIG_PATH"
        echo "   -> Дія: Перевірте права доступу (chmod +r ...)."
    fi
    echo "-------------------------------------------------------------"
    exit 1
fi
