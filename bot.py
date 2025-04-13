import os
import aiohttp
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_USERNAME = os.getenv("BOT_USERNAME")  
DEFAULT_MODEL = "meta-llama/llama-4-maverick:free"  

MODELS = {
    "meta-llama/llama-4-maverick:free": "Llama 4 Maverick",
    "google/gemini-2.5-pro-exp-03-25:free": "Gemini 2.5 pro exp",
    "qwen/qwq-32b:free": "Qwen QwQ 32B"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я умный бот. Напиши мне любой вопрос\n"
        "Используйте /model, чтобы выбрать модель для генерации ответов.\n"
        "В группах обращайтесь ко мне через @" + BOT_USERNAME[1:] 
    )

async def model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(name, callback_data=model_id)]
        for model_id, name in MODELS.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите модель для генерации ответов:", reply_markup=reply_markup)
    
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    model_id = query.data
    if model_id in MODELS:
        context.user_data["model"] = model_id  
        await query.message.chat.send_message(f"Выбрана модель: {MODELS[model_id]}")
        await query.message.delete()
    else:
        await query.message.reply_text("Ошибка: модель не найдена.")
        await query.message.delete()

async def query_openrouter(message: str, model: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
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
        if message.reply_to_message and message.reply_to_message.from_user.username == BOT_USERNAME[1:]:
            pass 
        else:
            if not text.startswith(BOT_USERNAME):
                return 
            text = text[len(BOT_USERNAME):].strip() 
    if not text:
        await message.reply_text("Напиши мне что-нибудь, и я отвечу с помощью нейросети!")
        return
    model = context.user_data.get("model", DEFAULT_MODEL)
    thinking_message = await message.reply_text("Думаю...")
    response = await query_openrouter(text, model)

    try:
        await thinking_message.delete()
    except Exception as e:
        logger.error(f"Failed to delete thinking message: {str(e)}")
    await message.reply_text(response)

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("model", model))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
