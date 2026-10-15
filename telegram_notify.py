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


# Bảng giá chính chủ Anthropic, đơn vị: USD cho 1 triệu token.
# API không trả về giá/chi phí (usage chỉ có số token) nên phải giữ bảng giá ở đây.
# Nguồn: https://platform.claude.com/docs/en/about-claude/pricing — cập nhật 15/10/2026.
PRICING = {
    # model                 input   ghi cache 5m  ghi cache 1h  đọc cache   output
    "claude-fable-5-1":   ( 10.00,     12.50,        20.00,       0.25,      50.00),
    "claude-mythos-5-1":  ( 10.00,     12.50,        20.00,       0.25,      50.00),
    "claude-fable-5":     ( 10.00,     12.50,        20.00,       1.00,      50.00),
    "claude-mythos-5":    ( 10.00,     12.50,        20.00,       1.00,      50.00),

    "claude-opus-5-5":    (  4.00,      5.00,         8.00,       0.20,      20.00),
    "claude-opus-5":      (  5.00,      6.25,        10.00,       0.50,      25.00),
    "claude-opus-4-8":    (  5.00,      6.25,        10.00,       0.50,      25.00),
    "claude-opus-4-7":    (  5.00,      6.25,        10.00,       0.50,      25.00),
    "claude-opus-4-6":    (  5.00,      6.25,        10.00,       0.50,      25.00),
    "claude-opus-4-5":    (  5.00,      6.25,        10.00,       0.50,      25.00),
    "claude-opus-4-1":    ( 15.00,     18.75,        30.00,       1.50,      75.00),
    "claude-opus-4":      ( 15.00,     18.75,        30.00,       1.50,      75.00),

    "claude-sonnet-5-5":  (  2.00,      2.50,         4.00,       0.10,      10.00),
    "claude-sonnet-5":    (  2.00,      2.50,         4.00,       0.20,      10.00),
    "claude-sonnet-4-6":  (  3.00,      3.75,         6.00,       0.30,      15.00),
    "claude-sonnet-4-5":  (  3.00,      3.75,         6.00,       0.30,      15.00),
    "claude-sonnet-4":    (  3.00,      3.75,         6.00,       0.30,      15.00),

    "claude-haiku-5-5":   (  0.10,      0.125,        0.20,       0.01,       0.50),
    "claude-haiku-4-5":   (  1.00,      1.25,         2.00,       0.10,       5.00),
    "claude-3-5-haiku":   (  0.80,      1.00,         1.60,       0.08,       4.00),
}
# Haiku 5.5 khi prompt dài hơn 100K token (tính cả cache) thì dùng giá này
#                       input   ghi cache 5m  ghi cache 1h  đọc cache   output
HAIKU_5_5_LONG =      (  0.50,      0.625,        1.00,       0.05,       2.50)


def model_price(model, prompt_tokens):
    """Tìm giá theo tiền tố dài nhất của model id (bỏ qua hậu tố ngày, [1m]...)."""
    keys = [k for k in PRICING if model.startswith(k)]
    if not keys:
        return None
    key = max(keys, key=len)
    if key == "claude-haiku-5-5" and prompt_tokens > 100_000:
        return HAIKU_5_5_LONG
    return PRICING[key]


def message_cost(model, u):
    """Chi phí 1 response theo giá model. None nếu model chưa có trong bảng giá.
    shortcut: chưa tính phụ phí fast mode / inference_geo=us (x1.1) / long-context Sonnet 4.5 trở về trước."""
    inp = u.get("input_tokens", 0) or 0
    cw = u.get("cache_creation_input_tokens", 0) or 0
    cr = u.get("cache_read_input_tokens", 0) or 0
    out = u.get("output_tokens", 0) or 0
    price = model_price(model, inp + cw + cr)
    if price is None:
        return None
    p_in, p_w5, p_w1, p_read, p_out = price
    # Tách ghi cache 5m / 1h nếu transcript có; không có thì coi là 5m
    split = u.get("cache_creation") or {}
    cw_1h = split.get("ephemeral_1h_input_tokens", 0) or 0
    cw_5m = cw - cw_1h
    return (inp * p_in + cw_5m * p_w5 + cw_1h * p_w1 + cr * p_read + out * p_out) / 1_000_000


def get_session_token_usage(transcript_file, session_id, cwd):
    """Tính token usage + chi phí từ transcript.
    Trả về ((input, cache_write, cache_read, output), cost_usd, models_chưa_có_giá)."""
    try:
        if not transcript_file or not os.path.exists(transcript_file):
            # Fallback: tự dựng đường dẫn, tôn trọng CLAUDE_CONFIG_DIR (vd ~/.claude-official)
            config_dir = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
            cwd_normalized = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
            transcript_file = os.path.join(config_dir, "projects", cwd_normalized, f"{session_id}.jsonl")
        if not os.path.exists(transcript_file):
            return (0, 0, 0, 0), 0.0, set()

        # Một response bị ghi thành nhiều dòng cùng message.id → chỉ tính 1 lần
        usage_by_id = {}
        with open(transcript_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    msg = json.loads(line).get("message", {})
                    if isinstance(msg, dict) and isinstance(msg.get("usage"), dict):
                        usage_by_id[msg.get("id") or len(usage_by_id)] = (msg.get("model") or "", msg["usage"])
                except (json.JSONDecodeError, AttributeError):
                    continue

        totals = [0, 0, 0, 0]
        cost = 0.0
        unknown_models = set()
        for model, u in usage_by_id.values():
            tokens = [
                u.get("input_tokens", 0) or 0,
                u.get("cache_creation_input_tokens", 0) or 0,
                u.get("cache_read_input_tokens", 0) or 0,
                u.get("output_tokens", 0) or 0,
            ]
            if not any(tokens):
                continue  # vd model "<synthetic>" không tốn token
            totals = [a + b for a, b in zip(totals, tokens)]
            c = message_cost(model, u)
            if c is None:
                unknown_models.add(model or "?")
            else:
                cost += c
        return tuple(totals), cost, unknown_models
    except Exception:
        return (0, 0, 0, 0), 0.0, set()


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
        (input_tokens, cache_write, cache_read, output_tokens), cost, unknown_models = get_session_token_usage(
            hook_data.get("transcript_path", ""), session_id, cwd
        )
        all_input = input_tokens + cache_write + cache_read
        total_tokens = all_input + output_tokens

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
            # Phiên nhỏ (< 1 cent) cần thêm số lẻ mới thấy được chi phí
            cost_str = f"${cost:.2f}" if cost >= 0.01 else f"${cost:.4f}"
            lines.extend([
                f"🔢 <b>Tokens:</b>  {format_tokens(total_tokens)}"
                f"  (↓{format_tokens(all_input)} / ↑{format_tokens(output_tokens)})",
                f"💾 <b>Cache:</b>  đọc {format_tokens(cache_read)} / ghi {format_tokens(cache_write)}",
                f"💰 <b>Chi phí ước tính:</b>  ~{cost_str}",
            ])
            if unknown_models:
                lines.append(f"⚠️ Chưa có giá cho: <code>{', '.join(sorted(unknown_models))}</code>")

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
