import os
import aiohttp
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токены и настройки из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_USERNAME = os.getenv("BOT_USERNAME")  # Имя бота, например @YourBotName
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")  # Модель по умолчанию

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
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "Ты умный и полезный ассистент. Отвечай кратко, но информативно, как эксперт в теме."},
            {"role": "user", "content": message}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                logger.info(f"OpenRouter API response status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"OpenRouter API response: {result}")
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                    return f"Ошибка при обращении к нейросети: {response.status} - {error_text}"
    except Exception as e:
        logger.error(f"Exception in query_openrouter: {str(e)}")
        return f"Произошла ошибка при обращении к нейросети: {str(e)}"

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

    # Отправляем временное сообщение "Думаю..." и сохраняем его
    thinking_message = await message.reply_text("Думаю... 🤔")

    # Отправляем запрос к OpenRouter.ai
    response = await query_openrouter(text)

    # Пытаемся удалить сообщение "Думаю..."
    try:
        await thinking_message.delete()
    except Exception as e:
        logger.error(f"Failed to delete thinking message: {str(e)}")
        # Если удаление не удалось, оставляем сообщение, но продолжаем

    # Отправляем ответ
    await message.reply_text(response)

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
