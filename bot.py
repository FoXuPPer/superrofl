import asyncio
import os
import speedtest
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Получаем токен из переменной окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Измерить скорость", callback_data="measure_speed")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я бот, который измерит скорость интернета на сервере, где я запущен. 📡\n"
        "Нажми на кнопку ниже, чтобы начать тест.",
        reply_markup=reply_markup
    )

# Функция для проведения теста скорости
def run_speedtest():
    try:
        # Инициализируем Speedtest
        st = speedtest.Speedtest()
        st.get_best_server()  # Находим лучший сервер для теста

        # Измеряем пинг
        ping = st.results.ping

        # Измеряем скорость загрузки (download) и переводим в Мбит/с
        download_speed = st.download() / 1_000_000  # Переводим из бит/с в Мбит/с

        # Измеряем скорость выгрузки (upload) и переводим в Мбит/с
        upload_speed = st.upload() / 1_000_000  # Переводим из бит/с в Мбит/с

        return download_speed, upload_speed, ping
    except Exception as e:
        return None, None, None

# Функция для обработки нажатия на кнопку
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "measure_speed":
        # Сообщение о начале теста
        await query.message.reply_text("Запускаю тест скорости интернета... Это может занять около 30 секунд. 📏")

        # Запускаем тест скорости
        download_speed, upload_speed, ping = run_speedtest()

        if download_speed is None or upload_speed is None:
            # Если тест не удался
            result_message = "Произошла ошибка при выполнении теста скорости. Попробуй снова позже. 😔"
        else:
            # Формируем результат
            result_message = (
                f"📊 Результаты теста скорости интернета:\n\n"
                f"Входящая скорость: {download_speed:.2f} Мбит/с\n"
                f"Исходящая скорость: {upload_speed:.2f} Мбит/с\n"
                f"Пинг: {ping:.2f} мс\n\n"
                f"Эти результаты показывают скорость интернета на сервере, где я запущен. "
                f"Твоя реальная скорость может отличаться."
            )

        # Добавляем кнопку для повторного теста
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
