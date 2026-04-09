# Claude Code — Telegram Notification

Gửi thông báo Telegram tự động mỗi khi Claude Code hoàn thành công việc.  
Cài **1 lần** vào `~/.claude/`, hoạt động cho **tất cả project** trên máy.

---

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

---

## Cài đặt

### 1. Chuẩn bị Telegram

| Cần lấy | Cách lấy |
|---|---|
| **Bot Token** | Nhắn `/newbot` cho [@BotFather](https://t.me/BotFather) |
| **Chat ID** | Nhắn `/start` cho [@userinfobot](https://t.me/userinfobot) |

### 2. Chạy script

**Windows:**
```powershell
.\install.ps1
```

**Linux / macOS:**
```bash
chmod +x install.sh && ./install.sh
```

Script sẽ hỏi Bot Token và Chat ID, rồi tự động cài vào `~/.claude/`.

### 3. Restart Claude Code

Hook có hiệu lực ngay sau khi restart.

---

## Cài đặt thủ công

<details>
<summary>Xem hướng dẫn</summary>

1. Copy `telegram_notify.py` vào `~/.claude/`

2. Tạo `~/.claude/config.json`:
   ```json
   {
     "bot_token": "YOUR_TOKEN",
     "chat_id": "YOUR_CHAT_ID"
   }
   ```

3. Thêm vào `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "Stop": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "python \"C:\\Users\\<tên>/.claude/telegram_notify.py\"",
               "timeout": 15
             }
           ]
         }
       ]
     }
   }
   ```

</details>

---

## Gỡ cài đặt

Xóa 2 file và bỏ phần hook trong `settings.json`:
```
~/.claude/telegram_notify.py
~/.claude/config.json
```

---

## Yêu cầu

- Python 3.6+ (không cần cài thêm package)
- Claude Code đã được cài đặt

## License

MIT
