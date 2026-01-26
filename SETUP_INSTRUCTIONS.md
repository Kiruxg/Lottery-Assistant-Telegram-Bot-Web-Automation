# Quick Setup Guide

## ⚠️ Missing Telegram Credentials

The `.env` file needs your Telegram bot credentials. Here's how to set it up:

### Quick Steps:

1. **Create `.env` file** (if it doesn't exist):
   ```powershell
   Copy-Item env.example .env
   ```

2. **Get Telegram Bot Token:**
   - Open Telegram, search for **@BotFather**
   - Send `/newbot` and follow instructions
   - Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

3. **Get Your Chat ID:**
   - Send a message to your bot on Telegram
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Find `"chat":{"id":123456789}` - that number is your chat ID

4. **Edit `.env` file:**
   - Open `.env` in Notepad or any text editor
   - Replace `your_bot_token_here` with your actual token
   - Replace `your_chat_id_here` with your actual chat ID
   - Save the file

5. **Test:**
   ```powershell
   python main.py test
   ```

### Detailed Instructions

See `TELEGRAM_SETUP.md` for step-by-step instructions with screenshots.

### Current Error

```
ValueError: TELEGRAM_BOT_TOKEN must be provided
```

This means the `.env` file either:
- Doesn't exist
- Has placeholder values (`your_bot_token_here`)
- Has incorrect format

Fix by editing `.env` and adding your real credentials!
