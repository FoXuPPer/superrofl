import os
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_USERNAME = os.getenv("BOT_USERNAME")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот с нейросетью. Напиши мне любой вопрос, и я отвечу! 🤖\n"
        "В группах обращайся ко мне через @" + BOT_USERNAME[1:]  # Убираем @ из имени
    )
    
async def query_openrouter(message: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_MODEL, 
        "messages": [{"role": "user", "content": message}]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return "Ошибка при обращении к нейросети. Попробуйте снова позже."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text

    if message.chat.type in ["group", "supergroup"]:
        if not text.startswith(BOT_USERNAME):
            return 
        text = text[len(BOT_USERNAME):].strip()

    if not text:
        await message.reply_text("Напишите мне что-нибудь, и я отвечу")
        return
    thinking_message = await message.reply_text("ща")
    response = await query_openrouter(text)
    await thinking_message.delete()
    await message.reply_text(response)

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
