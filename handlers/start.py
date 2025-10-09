# ЗАМЕНИТЕ содержимое handlers/start.py на это:
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from config import START, CITY
from utils.keyboards import get_accept_terms_keyboard, get_city_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = get_accept_terms_keyboard()
    
    welcome_text = (
        "Приветствуем тебя, дорогой пользователь! 👋\n\n"
        "Перед использованием ознакомься с нашей политикой конфиденциальности и пользовательским соглашением.\n\n"
        "Нажми кнопку «✅ ПРИНЯТЬ УСЛОВИЯ» для продолжения."
    )
    
    await update.message.reply_text(welcome_text, reply_markup=keyboard)
    return START

async def accept_terms_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстового принятия условий"""
    user_input = update.message.text.lower()
    
    if user_input in ['ок', 'ok', 'хорошо', 'согласен', 'принимаю']:
        user_id = update.message.from_user.id
        from config import user_data
        user_data[user_id] = {}
        
        await update.message.reply_text(
            "✅ Вы приняли условия использования!\n\nОтлично! Теперь выбери свой город:",
            reply_markup=get_city_keyboard()
        )
        
        return CITY
    else:
        await update.message.reply_text("Пожалуйста, нажмите кнопку «✅ ПРИНЯТЬ УСЛОВИЯ» для продолжения.")
        return START

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия на инлайн-кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "accept_terms":
        user_id = query.from_user.id
        from config import user_data
        user_data[user_id] = {}
        
        await query.edit_message_text("✅ Вы приняли условия использования!\n\nОтлично! Теперь выбери свой город:")
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🗺️ Выбери город из списка:",
            reply_markup=get_city_keyboard()
        )
        
        return CITY

# Обработчики должны быть объявлены ПОСЛЕ определения функций
start_handlers = [
    CallbackQueryHandler(button_handler, pattern='^accept_terms$'),
    MessageHandler(filters.TEXT & ~filters.COMMAND, accept_terms_text)
]