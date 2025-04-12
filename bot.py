import os
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Получаем токены из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_USERNAME = os.getenv("BOT_USERNAME")  # Имя бота, например @YourBotName

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот с нейросетью. Напиши мне любой вопрос, и я отвечу! 🤖\n"
        "В группах обращайся ко мне через @" + BOT_USERNAME[1:]  # Убираем @ из имени
    )

# Функция для взаимодействия с OpenRouter.ai
async def query_openrouter(message: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",  # Бесплатная модель
        "messages": [{"role": "user", "content": message}]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return "Ошибка при обращении к нейросети. Попробуй снова позже."

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text

    # Проверяем, что это группа и сообщение адресовано боту через @названиебота
    if message.chat.type in ["group", "supergroup"]:
        if not text.startswith(BOT_USERNAME):
            return  # Игнорируем сообщения, не адресованные боту
        text = text[len(BOT_USERNAME):].strip()  # Убираем @названиебота из текста

    # Если текст пустой, просим написать что-то
    if not text:
        await message.reply_text("Напиши мне что-нибудь, и я отвечу с помощью нейросети!")
        return

    # Отправляем запрос к OpenRouter.ai
    await message.reply_text("Думаю... 🤔")
    response = await query_openrouter(text)
    await message.reply_text(response)

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
