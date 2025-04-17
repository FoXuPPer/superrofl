import os
import aiohttp
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
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
    "meta-llama/llama-3.1-8b-instruct:free": "LLaMA 3.1 (тупой)",
    "google/gemma-2-9b-it:free": "Gemma 2 (?)", 
    "qwen/qwen-2-72b-instruct:free": "Qwen 2 (?)",
    "meta-llama/llama-4-maverick:free": "LLaMa 4 (умный)",
    "google/gemini-2.5-pro-exp-03-25:free": "Gemini 2.5 pro (умный)"
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

async def query_openrouter(message: str, model: str, context: ContextTypes.DEFAULT_TYPE) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": "Ты умный и полезный ассистент. Отвечай кратко, но информативно, как эксперт в теме."}
    ]
    
    if "chat_history" in context.user_data and context.user_data["chat_history"]:
        for entry in context.user_data["chat_history"]:
            messages.append({"role": "user", "content": entry["question"]})
            messages.append({"role": "assistant", "content": entry["response"]})
    
    messages.append({"role": "user", "content": message})
    
    data = {
        "model": model,
        "messages": messages
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                logger.info(f"OpenRouter API response status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"OpenRouter API response: {result}")
                    if "choices" in result and result["choices"]:
                        return result["choices"][0]["message"]["content"]
                    else:
                        logger.error(f"OpenRouter API response missing 'choices': {result}")
                        return "Ошибка: ответ от нейросети не содержит ожидаемых данных. Попробуйте выбрать другую модель с помощью /model."
                else:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                    if response.status == 429:
                        return "Ошибка: превышен лимит запросов. Подождите немного или выберите другую модель с помощью /model."
                    elif response.status == 401:
                        return "Ошибка: неверный API-ключ. Пожалуйста, сообщите администратору бота."
                    else:
                        return f"Ошибка при обращении к нейросети: {response.status} - {error_text}"
    except Exception as e:
        logger.error(f"Exception in query_openrouter: {str(e)}")
        return f"Произошла ошибка при обращении к нейросети: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text
    logger.info(f"Получено сообщение: {text}")

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

    if "chat_history" not in context.user_data:
        context.user_data["chat_history"] = []
        logger.info("Инициализирована пустая история переписки")

    model = context.user_data.get("model", DEFAULT_MODEL)

    thinking_message = await message.reply_text("Думаю...")

    response = await query_openrouter(text, model, context)

    context.user_data["chat_history"].append({
        "question": text,
        "response": response
    })
    logger.info(f"Добавлено в историю: вопрос='{text}', ответ='{response}'")
    if len(context.user_data["chat_history"]) > 10:
        context.user_data["chat_history"] = context.user_data["chat_history"][-10:]

    try:
        await thinking_message.delete()
    except Exception as e:
        logger.error(f"Failed to delete thinking message: {str(e)}")

    # Отправляем ответ
    await message.reply_text(response)
    
async def who(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    logger.info(f"Команда !кто/!кого получена: {message.text}")
    
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply_text("Эта команда работает только в группах.")
        return

    text = message.text
    command = "кто" if text.startswith("!кто") else "кого"
    command_length = len(command) + 1  
    
    if len(text) <= command_length:
        await message.reply_text("Укажите вопрос после команды.")
        return
    question = text[command_length:].strip() 
    
    try:
        chat_admins = await context.bot.get_chat_administrators(message.chat.id)

        all_members = [admin.user for admin in chat_admins if not admin.user.is_bot]
        logger.info(f"Доступные участники (администраторы): {len(all_members)}")
        
        if not all_members:
            await message.reply_text("Не удалось найти участников среди администраторов группы.")
            return

        if command == "кто":
            random_member = random.choice(all_members)
            
            user_id = str(random_member.id)
            if "nicknames" in context.chat_data and user_id in context.chat_data["nicknames"]:
                display_name = context.chat_data["nicknames"][user_id]
            else:
                display_name = random_member.first_name
            
            mention = f"[{display_name}](tg://user?id={random_member.id})"
            
            intro = random.choice(INTROS)
            response = f"{intro}, что {mention} {question}"
            
        else:  
            if len(all_members) < 2:
                await message.reply_text("Нужно как минимум два участника для команды !кого.")
                return
            
            member1 = random.choice(all_members)
            all_members.remove(member1) 
            member2 = random.choice(all_members)
            
            user1_id = str(member1.id)
            user2_id = str(member2.id)
            display_name1 = context.chat_data["nicknames"][user1_id] if "nicknames" in context.chat_data and user1_id in context.chat_data["nicknames"] else member1.first_name
            display_name2 = context.chat_data["nicknames"][user2_id] if "nicknames" in context.chat_data and user2_id in context.chat_data["nicknames"] else member2.first_name
            
            mention1 = f"[{display_name1}](tg://user?id={member1.id})"
            mention2 = f"[{display_name2}](tg://user?id={member2.id})"
            
            intro = random.choice(INTROS)
            question_lower = question.lower()
            if question_lower.startswith("я ") or question_lower.startswith("ты "):
                action = question.split(" ", 1)[1] if " " in question else question
                response = f"{intro}, что {mention1} {action} {mention2}"
            else:
                response = f"{intro}, что {mention2} {question}"
        
        await message.reply_text(response, parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"Ошибка в команде !кто/!кого: {str(e)}")
        await message.reply_text("Произошла ошибка при выборе участника.")

async def set_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply_text("Эта команда работает только в группах.")
        return
    
    text = message.text
    nickname = text[4:].strip() if len(text) > 4 else "" 
    
    user = message.from_user
    user_id = str(user.id)
    real_name = user.first_name  
    mention = f"[{real_name}](tg://user?id={user_id})"
    
    if "nicknames" not in context.chat_data:
        context.chat_data["nicknames"] = {}
    
    if not nickname:
        if user_id in context.chat_data["nicknames"] and context.chat_data["nicknames"][user_id]:
            current_nickname = context.chat_data["nicknames"][user_id]
            response = f"🗓 Ник пользователя {mention} : «{current_nickname}»"
        else:
            response = f"🗓 У пользователя {mention} пока нет ника."
        await message.reply_text(response, parse_mode="Markdown")
        return
    
    context.chat_data["nicknames"][user_id] = nickname
    logger.info(f"Установлен ник для {user_id}: {nickname}")
    
    response = f"✅ Ник {mention} изменён на «{nickname}»"
    await message.reply_text(response, parse_mode="Markdown")

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    if "chat_history" not in context.user_data or not context.user_data["chat_history"]:
        await message.reply_text("История переписки с нейросетью пуста. Задай мне вопрос, чтобы начать!")
        return

    history_text = "📜 История переписки с нейросетью:\n\n"
    for i, entry in enumerate(context.user_data["chat_history"], 1):
        history_text += f"{i}. **Вопрос:** {entry['question']}\n**Ответ:** {entry['response']}\n\n"
    
    await message.reply_text(history_text, parse_mode="Markdown")

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    web_app = WebAppInfo(url="https://megagame-production.up.railway.app/")
    button = InlineKeyboardButton(text="Играть в Agar.io", web_app=web_app)
    keyboard = InlineKeyboardMarkup([[button]])
    
    await message.reply_text("Нажмите кнопку, чтобы запустить Agar.io", reply_markup=keyboard)

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("model", model))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.Regex(r'^!(кто|кого)\b'), who))
    app.add_handler(MessageHandler(filters.Regex(r'^!ник\b'), set_nickname))
    app.add_handler(MessageHandler(filters.Regex(r'^!история\b'), show_history))
    app.add_handler(MessageHandler(filters.Regex(r'^!игра\b'), start_game))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
