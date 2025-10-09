##[file name]: main.py
import logging
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes,
    ConversationHandler
)
from config import BOT_TOKEN, START, CITY, AGE, GENDER, NAME, DESCRIPTION, PHOTOS, MAIN_MENU, EDIT_PROFILE, EDIT_DESCRIPTION, EDIT_PHOTOS, VIEWING_PROFILES, SUPERLIKE_MESSAGE
from handlers.start import start, start_handlers
from handlers.registration import registration_handlers
from handlers.profile import profile_handlers
from handlers.menu import menu_handlers
from handlers.search import search_handlers
from handlers.like_handlers import like_handlers
from utils.keyboards import get_main_menu_keyboard

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def state_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для отладки текущего состояния"""
    user_id = update.message.from_user.id
    current_state = await context.application.persistence.get_conversation("main_conversation", (user_id, user_id))
    
    await update.message.reply_text(
        f"🔧 ТЕКУЩЕЕ СОСТОЯНИЕ: {current_state}\n"
        f"🔧 USER ID: {user_id}",
        reply_markup=get_main_menu_keyboard()
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    error = context.error
    logger.error(f"Ошибка: {error}", exc_info=True)
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла ошибка. Попробуйте позже."
            )
        except:
            pass

def main():
    print("🚀 ЗАПУСКАЕМ УЛУЧШЕННЫЙ DATING БОТ...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("state", state_debug))
    
    # Правильные состояния ConversationHandler
    states = {
        START: start_handlers,
        CITY: [registration_handlers[0]],
        AGE: [registration_handlers[1]],
        GENDER: [registration_handlers[2]],
        NAME: [registration_handlers[3]],
        DESCRIPTION: [registration_handlers[4]],
        PHOTOS: registration_handlers[5:7],
        MAIN_MENU: menu_handlers,  # Только обработчики меню
        EDIT_PROFILE: [profile_handlers[0]],
        EDIT_DESCRIPTION: [profile_handlers[1]],
        EDIT_PHOTOS: profile_handlers[2:4],
        VIEWING_PROFILES: search_handlers,  # Только обработчики поиска
        SUPERLIKE_MESSAGE: [search_handlers[1]]
    }
    
    # ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states=states,
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    # 🔧 ДОБАВЛЯЕМ ОБРАБОТЧИКИ ДЛЯ УВЕДОМЛЕНИЙ О ЛАЙКАХ ОТДЕЛЬНО
    # Они работают в любом состоянии
    for handler in like_handlers:
        application.add_handler(handler)
    
    application.add_error_handler(error_handler)
    
    print("💕 УЛУЧШЕННЫЙ DATING БОТ ЗАПУЩЕН!")
    application.run_polling()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Безопасная отмена"""
    from config import user_data
    user_id = update.message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text('❌ Разговор прерван. Используйте /start для начала.')
    return ConversationHandler.END

if __name__ == '__main__':
    main()
##[file content end]