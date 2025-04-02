import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Получаем токен из переменной окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
 keyboard = [
 [InlineKeyboardButton("Запустить Speedtest", web_app={"url": "https://speedtestminiapp-production.up.railway.app"})]
 ]
 reply_markup = InlineKeyboardMarkup(keyboard)
 await update.message.reply_text(
 "Привет! Я бот, который поможет тебе измерить скорость интернета.\n"
 "Нажми на кнопку ниже, чтобы запустить тест скорости в мини-приложении.",
 reply_markup=reply_markup
 )

# Обработчик данных от Web App
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
 data = update.message.web_app_data.data
 results = json.loads(data)
 await update.message.reply_text(
 f"Результаты теста скорости из мини-приложения:\n\n"
 f"Входящая скорость: {results['download']} Мбит/с"
 )

def main():
 app = Application.builder().token(TOKEN).build()
 app.add_handler(CommandHandler("start", start))
 app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
 print("Бот запущен...")
 app.run_polling()

if __name__ == "__ main__":
 main()
