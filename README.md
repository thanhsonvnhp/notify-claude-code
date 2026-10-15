# Claude Code — Thông báo qua Telegram

Mỗi khi Claude Code làm xong một lượt, script sẽ gửi một tin nhắn Telegram cho bạn. Tin nhắn cho biết project nào, đã dùng bao nhiêu token và chi phí ước tính là bao nhiêu.

Chỉ cần cài **1 lần** vào `~/.claude/` là dùng được cho **mọi project** trên máy.

---

## Tin nhắn mẫu

```
  🤖  CLAUDE CODE
────────────────────
✅ Hoàn thành

📋 Chi tiết phiên làm việc
────────────────────
📁 Project:  my-project
📂 Đường dẫn:
    D:\my-project
🔢 Tokens:  974.6K  (↓962.8K / ↑11.8K)
💾 Cache:  đọc 672.9K / ghi 120.5K
💰 Chi phí ước tính:  ~$2.23

🕐 Thời gian
────────────────────
📅 Thứ Năm, 15/10/2026
⏰ 14:30:25
```

---

## Cài đặt

### 1. Chuẩn bị Telegram

| Cần lấy | Cách lấy |
|---|---|
| **Bot Token** | Nhắn `/newbot` cho [@BotFather](https://t.me/BotFather) |
| **Chat ID** | Nhắn `/start` cho [@userinfobot](https://t.me/userinfobot) |

### 2. Chạy script cài đặt

**Windows:**
```powershell
.\install.ps1
```

**Linux / macOS:**
```bash
chmod +x install.sh && ./install.sh
```

Script sẽ hỏi Bot Token và Chat ID, sau đó tự chép file vào `~/.claude/` và thêm hook vào `~/.claude/settings.json`.

### 3. Khởi động lại Claude Code

Hook chỉ có hiệu lực sau khi khởi động lại.

---

## Dùng cho nhiều thư mục cấu hình (ví dụ cá nhân và công ty)

Nếu bạn tách Claude Code thành nhiều thư mục cấu hình (ví dụ `~/.claude` cho cá nhân và `~/.claude-official` cho công ty, dùng biến `CLAUDE_CONFIG_DIR`), không cần cài thêm script. Chỉ cần thêm cùng một hook vào `settings.json` của thư mục còn lại, trỏ tới script đã cài trong `~/.claude`:

```json
"command": "python \"C:\\Users\\<tên>\\.claude\\telegram_notify.py\""
```

Script tự đọc đúng transcript của từng môi trường, vì Claude Code gửi kèm đường dẫn transcript (`transcript_path`) mỗi khi gọi hook.

Lưu ý: script luôn đọc `config.json` nằm cùng thư mục với nó. Nếu muốn mỗi môi trường gửi về một bot khác nhau, hãy chép script sang thư mục kia, tạo `config.json` riêng ở đó rồi trỏ hook vào bản chép này.

---

## Token và chi phí được tính thế nào

**Số token là số liệu thật.** Mỗi lần Claude trả lời, API trả về số token đã dùng và Claude Code ghi lại vào file transcript (`.jsonl`). Script đọc file này rồi cộng lại:

- **↓ (đầu vào):** toàn bộ token gửi lên, đã gồm cả phần đọc và ghi cache.
- **↑ (đầu ra):** token Claude viết ra.
- **Cache đọc:** phần nội dung lấy lại từ cache, giá rẻ hơn nhiều so với đầu vào thường.
- **Cache ghi:** phần nội dung được lưu vào cache, giá cao hơn đầu vào thường một chút.

**Chi phí là ước tính.** Anthropic chỉ trả về số token, không trả về số tiền. Vì vậy script nhân số token với bảng giá chính thức của từng model, đặt trong biến `PRICING` ở đầu file `telegram_notify.py`:

- Mỗi câu trả lời được tính theo đúng model đã dùng (Opus, Sonnet, Haiku...). Một phiên có đổi model giữa chừng vẫn tính đúng.
- Ghi cache 5 phút và 1 giờ có giá khác nhau, nên được tính riêng.
- Haiku 5.5 có giá cao hơn khi prompt dài hơn 100.000 token, script cũng đã tính phần này.
- Nếu gặp model chưa có trong bảng giá, tin nhắn sẽ báo `⚠️ Chưa có giá cho: <tên model>`. Khi đó cần thêm giá model đó vào `PRICING`.

Bảng giá lấy từ [trang Pricing của Anthropic](https://platform.claude.com/docs/en/about-claude/pricing), cập nhật ngày 15/10/2026. Khi Anthropic đổi giá hoặc ra model mới, bạn cần tự sửa `PRICING` rồi chép lại file vào `~/.claude/`.

Một số trường hợp con số sẽ lệch so với thực tế:

- Chưa tính phụ phí của fast mode và của `inference_geo=us` (x1.1).
- Nếu bạn dùng gói Pro/Max thì không bị tính tiền theo token. Con số chỉ cho biết lượng dùng đó tương đương bao nhiêu tiền nếu trả theo API.
- Nếu đi qua proxy hoặc bên trung gian, giá thực trả là giá của bên đó.

---

## Cài đặt thủ công

<details>
<summary>Xem hướng dẫn</summary>

1. Chép `telegram_notify.py` vào `~/.claude/`

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
               "command": "python \"C:\\Users\\<tên>\\.claude\\telegram_notify.py\"",
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

## Cập nhật phiên bản mới

Chạy lại `install.ps1` (hoặc `install.sh`), hoặc chép đè `telegram_notify.py` mới vào `~/.claude/`. Không cần sửa lại `settings.json`.

---

## Gỡ cài đặt

Xóa 2 file sau và bỏ phần hook trong `settings.json` (của mọi thư mục cấu hình đã thêm):
```
~/.claude/telegram_notify.py
~/.claude/config.json
```

---

## Yêu cầu

- Python 3.6+ (không cần cài thêm thư viện)
- Đã cài Claude Code

## License

MIT
