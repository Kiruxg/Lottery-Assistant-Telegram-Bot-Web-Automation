# Getting Your Telegram Bot Credentials

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the command: `/newbot`
3. Follow the prompts:
   - Choose a name for your bot (e.g., "My Lottery Assistant")
   - Choose a username (must end in 'bot', e.g., "my_lottery_bot")
4. **Copy the bot token** - it looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

## Step 2: Get Your Chat ID

### Method 1: Using getUpdates API (Recommended)

1. Replace `<YOUR_BOT_TOKEN>` with your actual bot token
2. Open this URL in your browser:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. **Before opening the URL**, send a message to your bot on Telegram (any message like "Hello")
4. Look for `"chat":{"id":123456789}` in the JSON response
5. Copy that number - that's your `TELEGRAM_CHAT_ID`

### Method 2: Using @userinfobot

1. Search for **@userinfobot** on Telegram
2. Start a conversation with it
3. It will show your user ID (this is your chat_id)

### Method 3: Using @getidsbot

1. Search for **@getidsbot** on Telegram
2. Start a conversation
3. It will show your chat ID

## Step 3: Configure .env File

1. Open `.env` file in a text editor
2. Replace the placeholder values:
   ```
   TELEGRAM_BOT_TOKEN=your_actual_token_here
   TELEGRAM_CHAT_ID=your_actual_chat_id_here
   ```
3. Save the file

## Step 4: Test Your Configuration

Run:
```bash
python main.py test
```

You should receive a test message on Telegram!

## Troubleshooting

### "TELEGRAM_BOT_TOKEN must be provided"
- Make sure `.env` file exists in the project root
- Check that `TELEGRAM_BOT_TOKEN=` line doesn't have extra spaces
- Verify the token doesn't have quotes around it

### "TELEGRAM_CHAT_ID must be provided"
- Make sure you've sent at least one message to your bot
- Double-check the chat ID is correct (it's usually a number)
- Try Method 1 above to get your chat ID

### Bot not responding
- Make sure you've started the bot: Send `/start` to your bot on Telegram
- Verify the bot token is correct
- Check that you're using the correct chat ID
