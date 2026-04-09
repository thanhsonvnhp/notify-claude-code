#!/usr/bin/env python3
"""
Telegram Notification Hook for Claude Code.
Cài đặt toàn cục vào ~/.claude/ — hoạt động cho mọi project.

File config: ~/.claude/config.json (chứa bot_token & chat_id)
"""

import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")


def load_config():
    """Đọc bot_token và chat_id từ config.json cùng thư mục (~/.claude/)."""
    if not os.path.exists(CONFIG_FILE):
        print(json.dumps({
            "systemMessage": "⚠️ Thiếu file ~/.claude/config.json — không gửi được Telegram"
        }))
        sys.exit(0)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    bot_token = cfg.get("bot_token", "").strip()
    chat_id = cfg.get("chat_id", "").strip()

    if not bot_token or not chat_id or "YOUR_" in bot_token:
        print(json.dumps({
            "systemMessage": "⚠️ Chưa cấu hình bot_token/chat_id trong ~/.claude/config.json"
        }))
        sys.exit(0)

    return bot_token, chat_id


def get_session_token_usage(session_id, cwd):
    """Tính tổng token usage từ transcript file của session."""
    try:
        home = os.path.expanduser("~")
        cwd_normalized = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
        project_dir = os.path.join(home, ".claude", "projects", cwd_normalized)

        if not os.path.exists(project_dir):
            return 0, 0

        transcript_file = os.path.join(project_dir, f"{session_id}.jsonl")
        if not os.path.exists(transcript_file):
            return 0, 0

        total_input = 0
        total_output = 0

        with open(transcript_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg = data.get("message", {})
                    if isinstance(msg, dict):
                        usage = msg.get("usage", {})
                        if isinstance(usage, dict):
                            total_input += usage.get("input_tokens", 0)
                            total_output += usage.get("output_tokens", 0)
                except (json.JSONDecodeError, AttributeError):
                    continue

        return total_input, total_output
    except Exception:
        return 0, 0


def estimate_cost(input_tokens, output_tokens):
    """Ước tính chi phí (USD). Giá mặc định: Sonnet 4 — $3/1M input, $15/1M output."""
    input_cost = (input_tokens / 1_000_000) * 3.0
    output_cost = (output_tokens / 1_000_000) * 15.0
    return input_cost + output_cost


def send_telegram_message(bot_token, chat_id, message):
    """Gửi tin nhắn qua Telegram Bot API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        req = urllib.request.Request(
            url,
            data=urllib.parse.urlencode(data).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode()
    except Exception as e:
        print(f"Error sending telegram: {e}", file=sys.stderr)
        return None


def format_tokens(value):
    """Format số token: 1234567 → 1.23M, 12345 → 12.3K."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,}"


def main():
    try:
        bot_token, chat_id = load_config()

        # Đọc JSON từ stdin (hook input)
        raw = sys.stdin.read()
        hook_data = json.loads(raw) if raw.strip() else {}

        # ── Bỏ qua subagent session ─────────────────────────────────────
        transcript_path = hook_data.get("transcript_path", "").replace("\\", "/")
        if "/subagents/" in transcript_path:
            sys.exit(0)
        # ─────────────────────────────────────────────────────────────────

        # Thời gian
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%d/%m/%Y")
        weekdays = [
            "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm",
            "Thứ Sáu", "Thứ Bảy", "Chủ Nhật",
        ]
        weekday_str = weekdays[now.weekday()]

        # Thư mục project
        cwd = hook_data.get("cwd") or os.getcwd()
        folder_name = os.path.basename(cwd) or cwd

        # Stop reason
        stop_reason = hook_data.get("stop_reason", "")
        reason_map = {
            "end_turn":      "✅ Hoàn thành",
            "max_tokens":    "⚠️ Đạt giới hạn token",
            "tool_use":      "🔧 Đang dùng tool",
            "stop_sequence": "🛑 Stop sequence",
        }
        reason_label = reason_map.get(stop_reason, "✅ Hoàn thành")

        # Token usage
        session_id = hook_data.get("session_id", "")
        input_tokens, output_tokens = get_session_token_usage(session_id, cwd)
        total_tokens = input_tokens + output_tokens

        # Build message
        lines = [
            "  🤖  <b>CLAUDE CODE</b>  ",
            "────────────────────",
            f"{reason_label}",
            "",
            "📋 <b>Chi tiết phiên làm việc</b>",
            "────────────────────",
            f"📁 <b>Project:</b>  <code>{folder_name}</code>",
            f"📂 <b>Đường dẫn:</b>",
            f"    <code>{cwd}</code>",
        ]

        if total_tokens > 0:
            cost = estimate_cost(input_tokens, output_tokens)
            lines.append(
                f"🔢 <b>Tokens:</b>  {format_tokens(total_tokens)}"
                f"  (↓{format_tokens(input_tokens)} / ↑{format_tokens(output_tokens)})"
            )
            lines.append(f"💰 <b>Chi phí ước tính:</b>  ~${cost:.4f}")

        lines.extend([
            "",
            "🕐 <b>Thời gian</b>",
            "────────────────────",
            f"📅 {weekday_str}, {date_str}",
            f"⏰ {time_str}",
        ])

        message = "\n".join(lines)
        send_telegram_message(bot_token, chat_id, message)

        print(json.dumps({
            "systemMessage": f"📬 Đã gửi thông báo Telegram lúc {time_str}",
            "suppressOutput": True,
        }))

    except Exception as e:
        print(json.dumps({"systemMessage": f"Telegram hook lỗi: {e}"}))
        sys.exit(0)


if __name__ == "__main__":
    main()
