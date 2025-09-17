import os
import telebot
from flask import Flask, request

TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I'm your bot for your personal logs everytime you enter/exit the campus!!✅")

# /help command
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
Available commands:
/start - Start the bot
/help - Show this help menu
/about - Learn more about this bot
"""
    bot.reply_to(message, help_text)

# /about command
@bot.message_handler(commands=['about'])
def send_about(message):
    bot.reply_to(message, "This bot was created by Kenneth Beliran. It’s hosted 24/7 on Render and designed to support projects like automation, data logging, and RFID-based systems. 🚀
")

# Fallback handler (for unknown text)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "I don’t understand that command. Type /help for options.")

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://telegram-bot-njfi.onrender.com' + TOKEN)
    return "!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
