import random
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Измерить скорость", callback_data="measure_speed")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Привет! Я бот, который измерит твою скорость интернета! \n"
        "Нажми на кнопку ниже, чтобы начать.",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 

    if query.data == "measure_speed":
        await query.message.reply_text("Измеряю скорость интернета, пожалуйста, подождите...")
        await asyncio.sleep(random.randint(10, 20))

        download_speed = random.randint(1, 1000)  # Входящая скорость (Мбит/с)
        upload_speed = random.randint(1, 1000)    # Исходящая скорость (Мбит/с)
        ping = random.randint(0, 9999)            # Пинг (мс)

        result_message = (
            f"📊 Результаты замера скорости интернета:\n\n"
            f"Входящая скорость: {download_speed} Мбит/с\n"
            f"Исходящая скорость: {upload_speed} Мбит/с\n"
            f"Пинг: {ping} мс\n\n"
        )

        keyboard = [[InlineKeyboardButton("Измерить снова", callback_data="measure_speed")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(result_message, reply_markup=reply_markup)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
