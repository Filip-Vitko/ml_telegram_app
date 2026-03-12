import telegram.ext
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_HTTP_API")

async def start(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot. How can I help you today?")

async def help(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
        /start -> Start the bot
        /help -> Show help
        """
    )

def main():
    application = telegram.ext.Application.builder().token(TOKEN).build()
    application.add_handler(telegram.ext.CommandHandler("start", start))
    application.add_handler(telegram.ext.CommandHandler("help", help))
    application.run_polling()


if __name__ == "__main__":
    main()

