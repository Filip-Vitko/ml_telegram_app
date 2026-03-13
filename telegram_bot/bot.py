import telegram.ext
import os
import requests
from telegram.ext import filters
from pathlib import Path

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

async def chat(update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    prompt = (update.message.text).strip()
    if not prompt:
        await update.message.reply_text("Please provide a prompt to chat with the bot.")
        return

    try:
        r = requests.post(f"{os.getenv("API_URL")}/chat", json={"prompt": prompt})
        r.raise_for_status()
        data = r.json()
        answer = data.get("response",) or "(empty response)"
        await update.message.reply_text(answer)
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"LLM request failed: {e}")

def main():
    app = telegram.ext.Application.builder().token(TOKEN).build()
    send_message("Bot started!")
    app.add_handler(telegram.ext.CommandHandler("start", start))
    app.add_handler(telegram.ext.CommandHandler("help", help))
    app.add_handler(telegram.ext.MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()


if __name__ == "__main__":
    main()
