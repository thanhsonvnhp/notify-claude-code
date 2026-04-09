# Claude Code — Telegram Notification

Tự động gửi thông báo Telegram mỗi khi Claude Code hoàn thành công việc.
Cài đặt **toàn cục** vào `~/.claude/` — hoạt động cho **mọi project** trên máy.

## Tính năng

- 🔔 Thông báo tự động khi Claude Code dừng (hoàn thành, đạt giới hạn token, ...)
- 🔢 Hiển thị tổng token usage (input/output) của phiên làm việc
- 💰 Ước tính chi phí API
- 📁 Hiển thị tên project và đường dẫn
- 🚫 Tự động bỏ qua subagent sessions (chỉ thông báo main agent)
- ⚡ Không phụ thuộc thư viện ngoài — chỉ dùng Python standard library
- 🌍 Cài 1 lần, hoạt động cho tất cả project

## Cách hoạt động

```
~/.claude/                         ← Thư mục cấu hình toàn cục của Claude Code
├── settings.json                  ← Có hook "Stop" gọi telegram_notify.py
├── telegram_notify.py             ← Script gửi thông báo (được cài vào đây)
├── config.json                    ← Bot token & Chat ID (KHÔNG share)
├── config.example.json            ← File mẫu tham khảo
├── projects/                      ← Claude Code tự tạo
├── sessions/                      ← Claude Code tự tạo
└── ...
```

Khi Claude Code hoàn thành → hook "Stop" kích hoạt → chạy `telegram_notify.py` → gửi Telegram.

## Cài đặt

### Bước 1: Tạo Telegram Bot

1. Mở Telegram, tìm **@BotFather**
2. Gửi `/newbot` và làm theo hướng dẫn
3. Lưu lại **Bot Token** (dạng `123456789:ABCDef...`)

### Bước 2: Lấy Chat ID

1. Mở Telegram, tìm **@userinfobot**
2. Gửi `/start` — bot sẽ trả về **Chat ID** của bạn

### Bước 3: Chạy script cài đặt

**Windows (PowerShell):**
```powershell
cd path\to\notify-claude-code
.\install.ps1
```

**Linux / macOS:**
```bash
cd path/to/notify-claude-code
chmod +x install.sh
./install.sh
```

Script sẽ tự động:
- Copy `telegram_notify.py` vào `~/.claude/`
- Tạo `config.json` template trong `~/.claude/`
- Thêm hook "Stop" vào `~/.claude/settings.json` (merge, không ghi đè)

### Bước 4: Cấu hình Bot Token

Chỉnh sửa file `~/.claude/config.json`:

```json
{
  "bot_token": "123456789:ABCDefGHIjklMNOpqrSTUvwxYZ",
  "chat_id": "987654321"
}
```

### Bước 5: Khởi động lại Claude Code

Restart Claude Code — hook sẽ tự động chạy cho mọi project.

## Cài đặt thủ công

Nếu không muốn dùng script, làm theo các bước sau:

1. Copy `telegram_notify.py` vào `~/.claude/`
2. Tạo `~/.claude/config.json` với nội dung:
   ```json
   {
     "bot_token": "YOUR_TOKEN",
     "chat_id": "YOUR_CHAT_ID"
   }
   ```
3. Thêm hook vào `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "Stop": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "python \"$HOME/.claude/telegram_notify.py\"",
               "timeout": 15,
               "statusMessage": "Sending Telegram notification..."
             }
           ]
         }
       ]
     }
   }
   ```

## Thông báo mẫu

```
  🤖  CLAUDE CODE  
────────────────────
✅ Hoàn thành

📋 Chi tiết phiên làm việc
────────────────────
📁 Project:  my-project
📂 Đường dẫn:
    D:\my-project
🔢 Tokens:  125.4K  (↓120.1K / ↑5.3K)
💰 Chi phí ước tính:  ~$0.4398

🕐 Thời gian
────────────────────
📅 Thứ Tư, 09/04/2026
⏰ 14:30:25
```

## Gỡ cài đặt

1. Xóa `~/.claude/telegram_notify.py`
2. Xóa `~/.claude/config.json`
3. Xóa phần hook "telegram_notify" trong `~/.claude/settings.json`

## Bảo mật

- `config.json` chứa bot token — nằm trong `~/.claude/` (thư mục local, không thuộc git repo)
- Bot token chỉ có quyền gửi tin nhắn, không truy cập dữ liệu khác

## Yêu cầu

- Python 3.6+
- Không cần cài thêm package nào

## License

MIT
