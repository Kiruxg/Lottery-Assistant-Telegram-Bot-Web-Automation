# How to Get Your Telegram Chat ID

## What is a Chat ID?
- A **numeric identifier** (like `123456789`) that uniquely identifies your chat with the bot
- **NOT** the bot's username (like @JackpotAlertBot)
- **NOT** your Telegram username
- It's a number that Telegram uses internally to identify conversations

## Method 1: Using getUpdates API (Recommended)

1. **First, get your bot token** from `.env` file (the `TELEGRAM_BOT_TOKEN` value)

2. **Send a message to your bot** on Telegram:
   - Search for your bot (e.g., @JackpotAlertBot)
   - Send any message like "Hello" or "/start"

3. **Open this URL in your browser** (replace `<YOUR_BOT_TOKEN>` with your actual token):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   
   Example:
   ```
   https://api.telegram.org/bot123456789:ABCdefGHIjklMNOpqrsTUVwxyz/getUpdates
   ```

4. **Look for the chat ID** in the JSON response:
   ```json
   {
     "ok": true,
     "result": [
       {
         "update_id": 123456,
         "message": {
           "chat": {
             "id": 987654321,  ← THIS IS YOUR CHAT ID
             "first_name": "Your Name",
             "type": "private"
           }
         }
       }
     ]
   }
   ```

5. **Copy that number** (e.g., `987654321`) and put it in your `.env` file

## Method 2: Using @userinfobot

1. Search for **@userinfobot** on Telegram
2. Start a conversation with it
3. It will show your user ID - this is your chat ID for private chats

## Method 3: Using @getidsbot

1. Search for **@getidsbot** on Telegram
2. Start a conversation
3. It will show your chat ID

## Quick PowerShell Script

You can also use this PowerShell command (replace YOUR_BOT_TOKEN):

```powershell
$token = "YOUR_BOT_TOKEN"
Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getUpdates" | ConvertTo-Json -Depth 10
```

Then look for `"id"` in the `"chat"` object.

## Important Notes

- Chat ID is a **number**, not text
- For private chats, it's usually a 9-10 digit number
- You must send at least one message to your bot first
- The chat ID stays the same - you only need to get it once

## Your .env Should Look Like:

```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

NOT:
```
TELEGRAM_CHAT_ID=JackpotAlertBot  ❌ Wrong!
```
