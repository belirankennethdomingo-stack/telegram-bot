import os
import json
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from datetime import datetime

# ---------------- Google Sheets + Drive Setup ----------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Read credentials from environment variable
creds_json = os.environ.get("GOOGLE_CREDS_JSON")
if not creds_json:
    raise Exception("GOOGLE_CREDS_JSON environment variable not set!")

creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

gc = gspread.authorize(creds)
sheet = gc.open("ParkingBot Data").sheet1  # Replace with your Google Sheet name

gauth = GoogleAuth()
gauth.credentials = creds
drive = GoogleDrive(gauth)

# ---------------- Conversation States ----------------
NAME, STUDENT, PHONE, NUM_MOTOS, PLATES, ORCR = range(6)

# ---------------- Helper Function ----------------
def check_student_registered(student_number):
    """Return True if student number already exists in sheet"""
    try:
        records = sheet.col_values(2)  # column B = Student Number
        return student_number in records
    except Exception:
        return False

# ---------------- /start command ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm your bot for your personal logs every time you enter/exit the campus ✅"
    )

# ---------------- /help command ----------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
Available commands:
/start - Start the bot
/help - Show this help menu
/about - Learn more about this bot
/register - Register your personal info
"""
    await update.message.reply_text(help_text)

# ---------------- /about command ----------------
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I’m a bot deployed on Render, created by Kenneth Beliran 🎉"
    )

# ---------------- Fallback for unknown messages ----------------
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I don’t understand that command. Type /help for options.")

# ---------------- /register Handlers ----------------
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Let's register you.\nEnter your full name:")
    return NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Enter your student number:")
    return STUDENT

async def register_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    student_number = update.message.text
    if check_student_registered(student_number):
        await update.message.reply_text("❌ You are already registered.")
        return ConversationHandler.END
    context.user_data['student'] = student_number
    await update.message.reply_text("Enter your phone number:")
    return PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("How many motorcycles do you use? (Max 3)")
    return NUM_MOTOS

async def register_num_motos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        num = int(update.message.text)
        if num < 1 or num > 3:
            await update.message.reply_text("❌ Please enter a number between 1 and 3.")
            return NUM_MOTOS
        context.user_data['num_motos'] = num
        context.user_data['plates'] = []
        await update.message.reply_text(f"Enter plate number for motorcycle #1:")
        return PLATES
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number (1-3).")
        return NUM_MOTOS

async def register_plates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plate = update.message.text
    context.user_data['plates'].append(plate)
    if len(context.user_data['plates']) < context.user_data['num_motos']:
        next_num = len(context.user_data['plates']) + 1
        await update.message.reply_text(f"Enter plate number for motorcycle #{next_num}:")
        return PLATES
    else:
        await update.message.reply_text("Now, please upload a photo of your OR/CR:")
        return ORCR

async def register_orcr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    if not file:
        await update.message.reply_text("❌ Please upload a document file (photo/pdf).")
        return ORCR

    file_id = file.file_id
    file_name = file.file_name
    new_file = await context.bot.get_file(file_id)
    temp_path = f"temp_{file_name}"
    await new_file.download_to_drive(temp_path)

    gfile = drive.CreateFile({'title': file_name})
    gfile.SetContentFile(temp_path)
    gfile.Upload()
    gfile.InsertPermission({'type': 'anyone','value': 'anyone','role': 'reader'})
    orcr_link = gfile['alternateLink']
    context.user_data['orcr_link'] = orcr_link

    # Save to Google Sheets
    sheet.append_row([
        context.user_data['name'],
        context.user_data['student'],
        context.user_data['phone'],
        context.user_data['num_motos'],
        ', '.join(context.user_data['plates']),
        context.user_data['orcr_link'],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ])

    await update.message.reply_text(
        "✅ Registration complete! Your OR/CR has been uploaded.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ---------------- Main ----------------
def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        raise Exception("TELEGRAM_TOKEN environment variable not set!")

    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))

    # /register ConversationHandler
    register_conv = ConversationHandler(
        entry_points=[CommandHandler('register', register_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            STUDENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_student)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
            NUM_MOTOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_num_motos)],
            PLATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_plates)],
            ORCR: [MessageHandler(filters.Document.ALL, register_orcr)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(register_conv)

    # Fallback for unknown messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Start bot
    app.run_polling()

if __name__ == "__main__":
    main()
