import os
import aiohttp
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

INTROS = [
    "☝️ Я уверен",
    "🔭 Звёзды говорят",
    "🤔 Я думаю",
    "🔮 Ясно вижу"
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_USERNAME = os.getenv("BOT_USERNAME")  
DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct:free" 

MODELS = {
    "meta-llama/llama-3.1-8b-instruct:free": "LLaMA 3.1 8B (Free)",
    "google/gemma-2-9b-it:free": "Gemma 2 9B (Free)", 
    "qwen/qwen-2-72b-instruct:free": "Qwen 2 72B (Free)"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Приветствую! Я умный бот от создателей @treshdurov. Напишите мне любой вопрос.\n"
        "Используйте /model, чтобы выбрать модель для генерации ответов.\n"
        "В группах обращайтесь ко мне через @" + BOT_USERNAME[1:] + ", либо переслав любое моё сообщение."
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
                    # Проверяем наличие ключа 'choices'
                    if "choices" in result and result["choices"]:
                        return result["choices"][0]["message"]["content"]
                    else:
                        logger.error(f"OpenRouter API response missing 'choices': {result}")
                        return "Ошибка: ответ от нейросети не содержит ожидаемых данных. Попробуй выбрать другую модель с помощью /model."
                else:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                    if response.status == 429:
                        return "Ошибка: превышен лимит запросов. Подожди немного или выбери другую модель с помощью /model."
                    elif response.status == 401:
                        return "Ошибка: неверный API-ключ. Пожалуйста, сообщи администратору бота."
                    else:
                        return f"Ошибка при обращении к нейросети: {response.status} - {error_text}"
    except Exception as e:
        logger.error(f"Exception in query_openrouter: {str(e)}")
        return f"Произошла ошибка при обращении к нейросети: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text

    if message.chat.type in ["group", "supergroup"]:
        sender = message.from_user
        if not sender.is_bot: 
            if "group_members" not in context.chat_data:
                context.chat_data["group_members"] = {}
            context.chat_data["group_members"][sender.id] = sender

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
    
async def who(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    logger.info(f"Команда !кто получена: {message.text}")

    if message.chat.type not in ["group", "supergroup"]:
        await message.reply_text("Эта команда работает только в группах.")
        return
        
    text = message.text
    if len(text) <= 4: 
        await message.reply_text("Укажите вопрос после команды.")
        return
    question = text[4:].strip() 
    
    try:
        chat_members_count = await context.bot.get_chat_member_count(message.chat.id)
        if chat_members_count <= 1:
            await message.reply_text("В группе нет участников для выбора.")
            return
        
        if "group_members" not in context.chat_data:
            context.chat_data["group_members"] = {}
            logger.info("Инициализирован пустой group_members")

        sender = message.from_user
        if not sender.is_bot:
            context.chat_data["group_members"][sender.id] = sender
            logger.info(f"Добавлен участник в group_members: {sender.id}")

        all_members = [user for user in context.chat_data["group_members"].values() if not user.is_bot]
        logger.info(f"Доступные участники: {len(all_members)}")
        
        if not all_members:
            await message.reply_text("Не удалось найти участников. Попробуй позже, когда кто-то напишет в чат.")
            return
        
        random_member = random.choice(all_members)
        
        user_id = str(random_member.id)
        if "nicknames" in context.chat_data and user_id in context.chat_data["nicknames"]:
            display_name = context.chat_data["nicknames"][user_id]
        else:
            display_name = random_member.username if random_member.username else random_member.first_name
        
        mention = f"[{display_name}](tg://user?id={random_member.id})"
        
        intro = random.choice(INTROS)
        response = f"{intro}, что {mention} {question}"
        
        await message.reply_text(response, parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"Ошибка в команде !кто: {str(e)}")
        await message.reply_text("Произошла ошибка при выборе участника.")

async def set_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply_text("Эта команда работает только в группах.")
        return
    
    text = message.text
    if len(text) <= 4: 
        await message.reply_text("Укажите ник после команды.")
        return
    nickname = text[4:].strip() 
    
    if not nickname:
        await message.reply_text("Ник не может быть пустым.")
        return
    
    if "nicknames" not in context.chat_data:
        context.chat_data["nicknames"] = {}
    
    user = message.from_user
    user_id = str(user.id)
    real_name = user.username if user.username else user.first_name
    mention = f"[{real_name}](tg://user?id={user_id})"
    
    if user_id in context.chat_data["nicknames"]:
        old_nickname = context.chat_data["nicknames"][user_id]
        context.chat_data["nicknames"][user_id] = nickname
        response = f"✅ Ник {mention} изменён на «{nickname}»"
    else:
        context.chat_data["nicknames"][user_id] = nickname
        response = f"🗓 Ник пользователя {mention} : «{nickname}»"
    
    logger.info(f"Установлен ник для {user_id}: {nickname}")
    
    await message.reply_text(response, parse_mode="Markdown")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("model", model))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.Regex(r'^!кто\b'), who))
    app.add_handler(MessageHandler(filters.Regex(r'^!ник\b'), set_nickname))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
