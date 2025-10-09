##[file name]: handlers/menu.py

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from config import MAIN_MENU
from utils.keyboards import get_main_menu_keyboard, get_premium_payment_keyboard
from handlers.profile import show_profile
from handlers.search import start_search

async def start_talking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало общения - запускает поиск анкет"""
    print("🔍 ЗАПУСК ПОИСКА ИЗ ГЛАВНОГО МЕНЮ")
    return await start_search(update, context)

async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Служба поддержки"""
    support_text = (
        "🛠️ Служба поддержки Mireo\n\n"
        "Если у вас возникли вопросы, проблемы с работой бота или вы хотите пожаловаться на пользователя, "
        "пожалуйста, напишите нам на почту:\n\n"
        "📧 mireo_support@mail.ru\n\n"
        "Мы ответим вам в течение 24 часов!"
    )
    
    await update.message.reply_text(
        support_text,
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

async def buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка премиума"""
    premium_text = (
        "💫 Премиум подписка Mireo\n\n"
        "Откройте все возможности знакомств:\n\n"
        "⭐️ - Взаимные лайки на анкеты тех, кому ты понравился! ❤️‍🔥\n"
        "⭐️ - Возможность ставить суперлайки с сообщениями! 💌\n"
        "⭐️ - Статус «Premium💫» на вашей анкете\n"
        "⭐️ - Приоритет в поиске и рекомендациях\n\n"
        "Стоимость: 299 руб./месяц"
    )
    
    await update.message.reply_text(
        premium_text,
        reply_markup=get_premium_payment_keyboard()
    )

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка главного меню"""
    text = update.message.text
    
    print(f"🎯 ГЛАВНОЕ МЕНЮ: обработка '{text}' в состоянии MAIN_MENU")
    
    if text == "Моя анкета📄":
        print("🎯 Переход к показу профиля")
        return await show_profile(update, context)
    elif text == "Начать общение📝":
        print("🎯 Запуск поиска анкет")
        return await start_talking(update, context)
    elif text == "Купить Premium💫":
        print("🎯 Показ предложения премиума")
        await buy_premium(update, context)
        return MAIN_MENU
    elif text == "Служба поддержки⚙️":
        print("🎯 Показ службы поддержки")
        return await show_support(update, context)
    else:
        print(f"🎯 НЕИЗВЕСТНАЯ КОМАНДА: '{text}'")
        await update.message.reply_text(
            "Используйте кнопки меню для навигации",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU

# Обработчики только для текстовых сообщений в главном меню
menu_handlers = [
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
]

# Экспорт для импорта в main.py
__all__ = [
    'handle_main_menu',
    'menu_handlers'
]
##[file content end]