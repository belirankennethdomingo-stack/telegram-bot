import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot for you personal logs everytime you enter/exit the campus✅")

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
Available commands:
/start - Start the bot
/help - Show this help menu
/about - Learn more about this bot
"""
    await update.message.reply_text(help_text)

# /about command
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I’m a bot deployed on Render, created by Kenneth Beliran 🎉")

# Fallback for unknown messages
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I don’t understand that command. Type /help for options.")

def main():
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))

    # Fallback
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    app.run_polling()

if __name__ == "__main__":
    main()
