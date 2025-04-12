import os
import aiohttp
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_USERNAME = os.getenv("BOT_USERNAME") 
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free") 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я умный бот от создателей @treshdurov.\n"
        "Вы можете добавить меня в группу и обращаться со мной через @" + BOT_USERNAME[1:] 
    )

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text

    if message.chat.type in ["group", "supergroup"]:
        if not text.startswith(BOT_USERNAME):
            return  
        text = text[len(BOT_USERNAME):].strip() 

    if not text:
        await message.reply_text("Напишите мне что-нибудь, и я отвечу.")
        return

    thinking_message = await message.reply_text("ща")

    response = await query_openrouter(text)

    try:
        await thinking_message.delete()
    except Exception as e:
        logger.error(f"Failed to delete thinking message: {str(e)}")

    await message.reply_text(response)

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
