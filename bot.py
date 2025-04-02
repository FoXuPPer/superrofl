import random
import asyncio
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Получаем токен из переменной окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Измерить скорость (шутка)", callback_data="measure_speed_joke")],
        [InlineKeyboardButton("Измерить скорость (по-настоящему)", callback_data="measure_speed_real")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я бот, который может измерить твою скорость интернета! 😄\n"
        "Выбери, как хочешь измерить скорость: в виде шутки или по-настоящему.",
        reply_markup=reply_markup
    )

# Функция для обработки нажатия на кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "measure_speed_joke":
        # Первоапрельская шутка
        await query.message.reply_text("Измеряю скорость интернета... Пожалуйста, подожди! 📡")
        await asyncio.sleep(random.randint(10, 20))
        download_speed = random.randint(1, 1000)
        upload_speed = random.randint(1, 1000)
        ping = random.randint(0, 9999)
        result_message = (
            f"📊 Результаты замера скорости интернета:\n\n"
            f"Входящая скорость: {download_speed} Мбит/с\n"
            f"Исходящая скорость: {upload_speed} Мбит/с\n"
            f"Пинг: {ping} мс\n\n"
            f"С 1 апреля! 😂 Это, конечно, шутка, но ты можешь попробовать снова!"
        )
        keyboard = [
            [InlineKeyboardButton("Измерить снова (шутка)", callback_data="measure_speed_joke")],
            [InlineKeyboardButton("Измерить по-настоящему", callback_data="measure_speed_real")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(result_message, reply_markup=reply_markup)

    elif query.data == "measure_speed_real":
        # Настоящее измерение скорости
        await query.message.reply_text(
            "Начинаю настоящее измерение скорости! 📏\n"
            "Сначала я отправлю тебе файл для измерения скорости загрузки..."
        )

        # Измеряем пинг (время ответа на сообщение)
        start_time = time.time()
        ping_message = await query.message.reply_text("Измеряю пинг...")
        ping = (time.time() - start_time) * 1000  # Переводим в миллисекунды

        # Отправляем файл для измерения скорости загрузки
        file_size_mb = 5  # Размер файла в МБ
        file_path = "test_file.bin"
        
        # Создаём тестовый файл, если его нет
        if not os.path.exists(file_path):
            with open(file_path, "wb") as f:
                f.write(os.urandom(file_size_mb * 1024 * 1024))  # 5 МБ случайных данных

        start_time = time.time()
        with open(file_path, "rb") as f:
            await query.message.reply_document(document=f, caption="Скачай этот файл для теста скорости загрузки.")
        context.user_data["download_start_time"] = start_time
        context.user_data["file_size_mb"] = file_size_mb

        # Просим пользователя отправить файл для теста скорости выгрузки
        await query.message.reply_text(
            f"Пинг: {ping:.2f} мс\n"
            "Теперь отправь мне любой файл (например, фото или документ), чтобы измерить скорость выгрузки."
        )

# Функция для обработки отправленного пользователем файла
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "download_start_time" not in context.user_data:
        await update.message.reply_text("Сначала начни тест с помощью кнопки 'Измерить по-настоящему'!")
        return

    # Измеряем скорость выгрузки
    file = update.message.document
    if not file:
        await update.message.reply_text("Пожалуйста, отправь файл (например, фото или документ).")
        return

    start_time = time.time()
    file_size_mb = file.file_size / (1024 * 1024)  # Размер файла в МБ
    await update.message.reply_text("Получаю твой файл для теста скорости выгрузки...")

    # Скачиваем файл, чтобы измерить время
    new_file = await file.get_file()
    await new_file.download_to_drive()
    upload_time = time.time() - start_time

    # Вычисляем скорость выгрузки (upload speed)
    upload_speed = (file_size_mb * 8) / upload_time  # Мбит/с (1 МБ = 8 Мбит)

    # Вычисляем скорость загрузки (download speed) на основе времени, когда пользователь получил файл
    download_time = start_time - context.user_data["download_start_time"]
    download_speed = (context.user_data["file_size_mb"] * 8) / download_time  # Мбит/с

    # Формируем результат
    result_message = (
        f"📊 Результаты настоящего замера скорости интернета:\n\n"
        f"Входящая скорость: {download_speed:.2f} Мбит/с\n"
        f"Исходящая скорость: {upload_speed:.2f} Мбит/с\n"
        f"Пинг: {context.user_data.get('ping', 0):.2f} мс\n\n"
        "Это реальные показатели скорости через Telegram. Для более точного теста используй Speedtest.net!"
    )

    # Добавляем кнопки для повторного теста
    keyboard = [
        [InlineKeyboardButton("Измерить снова (шутка)", callback_data="measure_speed_joke")],
        [InlineKeyboardButton("Измерить снова (по-настоящему)", callback_data="measure_speed_real")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(result_message, reply_markup=reply_markup)

    # Очищаем данные
    context.user_data.clear()

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
