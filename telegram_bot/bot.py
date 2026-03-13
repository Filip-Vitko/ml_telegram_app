import telegram.ext
import os
from pathlib import Path
import requests
if Path(".env").exists():
    from dotenv import load_dotenv
    load_dotenv()

TOKEN = os.getenv("TELEGRAM_HTTP_API")
ID = os.getenv("CHAT_ID")

if not TOKEN:
    raise ValueError("TELEGRAM_HTTP_API environment variable is not set!")

if not ID:
    raise ValueError("CHAT_ID environment variable is not set!")

def send_message(message: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": ID,
        "text": message
    }
    response = requests.post(url, json=data)
    return response.json()

async def start(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot. How can I help you today?")

async def help(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start -> Start the bot"
        "/help -> Show help"
    )

def main():
    application = telegram.ext.Application.builder().token(TOKEN).build()
    send_message("Bot started!")
    application.add_handler(telegram.ext.CommandHandler("start", start))
    application.add_handler(telegram.ext.CommandHandler("help", help))
    application.run_polling()


if __name__ == "__main__":
    main()
