#!/bin/bash
# ============================================================
#  Claude Code - Telegram Notification Installer
#  Cài đặt toàn cục vào ~/.claude/ (Linux/macOS)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo ""
echo "========================================"
echo "  Claude Code - Telegram Notification   "
echo "  (Global Install -> ~/.claude/)        "
echo "========================================"
echo ""
echo "Target : $CLAUDE_DIR"
echo ""

# Kiểm tra ~/.claude tồn tại
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "[!] Không tìm thấy $CLAUDE_DIR"
    echo "    Hãy cài đặt Claude Code trước."
    exit 1
fi

# 1) Copy telegram_notify.py
cp -f "$SCRIPT_DIR/telegram_notify.py" "$CLAUDE_DIR/telegram_notify.py"
echo "[+] telegram_notify.py -> $CLAUDE_DIR/telegram_notify.py"

# 2) Tạo config.json nếu chưa có
if [ ! -f "$CLAUDE_DIR/config.json" ]; then
    cat > "$CLAUDE_DIR/config.json" << 'EOF'
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "chat_id": "YOUR_CHAT_ID_HERE"
}
EOF
    echo "[+] Đã tạo config.json (CẦN CHỈNH SỬA TOKEN!)"
else
    echo "[=] config.json đã tồn tại — giữ nguyên"
fi

# 4) Merge hook vào ~/.claude/settings.json
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
HOOK_COMMAND='python "$HOME/.claude/telegram_notify.py"'

if [ -f "$SETTINGS_FILE" ]; then
    if grep -q "telegram_notify" "$SETTINGS_FILE" 2>/dev/null; then
        echo "[=] settings.json đã có Telegram hook — giữ nguyên"
    else
        # Dùng python để merge JSON (tránh phụ thuộc jq)
        python3 -c "
import json, sys

with open('$SETTINGS_FILE', 'r') as f:
    settings = json.load(f)

hook_entry = {
    'hooks': [{
        'type': 'command',
        'command': '$HOOK_COMMAND',
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

print('[+] Đã thêm Telegram hook vào settings.json')
" 2>/dev/null || echo "[!] Lỗi merge — hãy thêm hook thủ công, xem README.md"
    fi
else
    cat > "$SETTINGS_FILE" << EOF
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"\$HOME/.claude/telegram_notify.py\"",
            "timeout": 15,
            "statusMessage": "Sending Telegram notification..."
          }
        ]
      }
    ]
  }
}
EOF
    echo "[+] Đã tạo settings.json với Telegram hook"
fi

echo ""
echo "========================================"
echo "  Cài đặt hoàn tất!                    "
echo "========================================"
echo ""
echo "Bước tiếp theo:"
echo "  1. Chỉnh sửa: $CLAUDE_DIR/config.json"
echo '     - Thay "YOUR_BOT_TOKEN_HERE" bằng token từ @BotFather'
echo '     - Thay "YOUR_CHAT_ID_HERE" bằng Chat ID từ @userinfobot'
echo "  2. Khởi động lại Claude Code — hook sẽ chạy cho mọi project"
echo ""
