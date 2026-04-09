#!/bin/bash
# ============================================================
#  Claude Code - Telegram Notification Installer
#  Cai dat toan cuc vao ~/.claude/ (Linux/macOS)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
CONFIG_FILE="$CLAUDE_DIR/config.json"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
SCRIPT_DST="$CLAUDE_DIR/telegram_notify.py"

echo ""
echo "========================================"
echo "  Claude Code - Telegram Notification"
echo "  Global Install -> $CLAUDE_DIR"
echo "========================================"
echo ""

# Kiem tra ~/.claude ton tai
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "[!] Khong tim thay $CLAUDE_DIR"
    echo "    Hay cai dat Claude Code truoc."
    exit 1
fi

# ── Buoc 1: Nhap Bot Token va Chat ID ────────────────────────────────────────
echo "BUOC 1: Cau hinh Telegram Bot"
echo "  - Lay bot token tu @BotFather tren Telegram"
echo "  - Lay chat ID tu @userinfobot tren Telegram"
echo ""

BOT_TOKEN=""
CHAT_ID=""

# Doc tu config.json hien tai neu da co
if [ -f "$CONFIG_FILE" ]; then
    EXISTING_TOKEN=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('bot_token',''))" 2>/dev/null || true)
    EXISTING_CHAT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('chat_id',''))" 2>/dev/null || true)

    if [ -n "$EXISTING_TOKEN" ] && echo "$EXISTING_TOKEN" | grep -qv "YOUR_"; then
        echo "  Da co config.json voi bot_token hien tai."
        read -p "  Giu nguyen? (Y/n): " KEEP
        if [ -z "$KEEP" ] || echo "$KEEP" | grep -qi "^y"; then
            BOT_TOKEN="$EXISTING_TOKEN"
            CHAT_ID="$EXISTING_CHAT"
            echo "  [=] Giu nguyen config hien tai."
        fi
    fi
fi

if [ -z "$BOT_TOKEN" ]; then
    read -p "  Nhap Bot Token: " BOT_TOKEN
    BOT_TOKEN=$(echo "$BOT_TOKEN" | xargs)
    if [ -z "$BOT_TOKEN" ]; then
        echo "[!] Bot Token khong duoc de trong."
        exit 1
    fi
    read -p "  Nhap Chat ID: " CHAT_ID
    CHAT_ID=$(echo "$CHAT_ID" | xargs)
    if [ -z "$CHAT_ID" ]; then
        echo "[!] Chat ID khong duoc de trong."
        exit 1
    fi
fi

# ── Buoc 2: Copy script ──────────────────────────────────────────────────────
echo ""
echo "BUOC 2: Cai dat files"

cp -f "$SCRIPT_DIR/telegram_notify.py" "$SCRIPT_DST"
echo "  [+] telegram_notify.py -> $SCRIPT_DST"

# ── Buoc 3: Ghi config.json ──────────────────────────────────────────────────
python3 -c "
import json
with open('$CONFIG_FILE', 'w') as f:
    json.dump({'bot_token': '$BOT_TOKEN', 'chat_id': '$CHAT_ID'}, f, indent=2)
"
echo "  [+] config.json -> $CONFIG_FILE"

# ── Buoc 4: Merge hook vao settings.json ──────────────────────────────────────
HOOK_CMD="python \"$SCRIPT_DST\""

if [ -f "$SETTINGS_FILE" ]; then
    if grep -q "telegram_notify" "$SETTINGS_FILE" 2>/dev/null; then
        echo "  [=] settings.json da co Telegram hook - giu nguyen"
    else
        python3 -c "
import json

with open('$SETTINGS_FILE', 'r') as f:
    settings = json.load(f)

hook_entry = {
    'hooks': [{
        'type': 'command',
        'command': 'python \"$SCRIPT_DST\"',
        'timeout': 15,
        'statusMessage': 'Sending Telegram notification...'
    }]
}

if 'hooks' not in settings:
    settings['hooks'] = {}
if 'Stop' not in settings['hooks']:
    settings['hooks']['Stop'] = []

settings['hooks']['Stop'].append(hook_entry)

with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
" && echo "  [+] Da them Telegram hook vao settings.json" \
  || echo "  [!] Loi merge - hay them hook thu cong, xem README.md"
    fi
else
    python3 -c "
import json
settings = {
    'hooks': {
        'Stop': [{
            'hooks': [{
                'type': 'command',
                'command': 'python \"$SCRIPT_DST\"',
                'timeout': 15,
                'statusMessage': 'Sending Telegram notification...'
            }]
        }]
    }
}
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
"
    echo "  [+] Da tao settings.json voi Telegram hook"
fi

# ── Ket qua ──────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  Cai dat hoan tat!"
echo "========================================"
echo ""
echo "  Restart lai Claude Code de hook co hieu luc."
echo ""
