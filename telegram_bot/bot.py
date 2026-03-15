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
API_URL = os.getenv("API_URL")

if not TOKEN:
    raise ValueError("TELEGRAM_HTTP_API environment variable is not set!")

if not ID:
    raise ValueError("CHAT_ID environment variable is not set!")

if not API_URL:
    raise ValueError("API_URL environment variable is not set!")

def send_message(message: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": ID,
        "text": message }
    response = requests.post(url, json=data)
    return response.json()

def get_model_name():
    try:
        r = requests.get(f"{API_URL}/models", timeout=5)
        r.raise_for_status()
        data = r.json()
        models = data.get("models", [])
        if models:
            return models[0]
        return None
    except Exception as e:
        print(f"Failed to get model name: {e}")
        return None

async def chat(update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    prompt = (update.message.text).strip()
    if not prompt:
        await update.message.reply_text("Please provide a prompt to chat with the bot.")
        return
    try:
        r = requests.post(f"{API_URL}/chat", json={"prompt": prompt})
        r.raise_for_status()
        data = r.json()
        answer = data.get("response",) or "(empty response)"
        await update.message.reply_text(answer)
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"LLM request failed: {e}")

def main():
    app = telegram.ext.Application.builder().token(TOKEN).build()
    model_name = get_model_name()
    if model_name:
        send_message(f"Bot started using model {model_name}!")
    else:
        send_message(f"Bot started! (Model not found)")
    app.add_handler(telegram.ext.MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()


if __name__ == "__main__":
    main()
