##[file name]: handlers/notifications.py

from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from config import db

async def send_like_notification(context: ContextTypes.DEFAULT_TYPE, from_user_id: int, to_user_id: int):
    """Отправляет уведомление о лайке"""
    print(f"🔔 ОТПРАВКА УВЕДОМЛЕНИЯ О ЛАЙКЕ: от {from_user_id} к {to_user_id}")
    
    # Добавляем в базу непрочитанный лайк
    db.add_pending_like(from_user_id, to_user_id)
    
    message_text = "Кто-то поставил лайк твоей анкете. Показать кто это был? 😮"
    
    # Импортируем клавиатуру внутри функции чтобы избежать циклических импортов
    from utils.keyboards import get_like_notification_keyboard
    
    await context.bot.send_message(
        chat_id=to_user_id,
        text=message_text,
        reply_markup=get_like_notification_keyboard()
    )

async def send_superlike_notification(context: ContextTypes.DEFAULT_TYPE, from_user_id: int, to_user_id: int, message: str):
    """Отправляет уведомление о суперлайке"""
    print(f"🔔 ОТПРАВКА УВЕДОМЛЕНИЯ О СУПЕРЛАЙКЕ: от {from_user_id} к {to_user_id}")
    
    # Добавляем в базу непрочитанный лайк
    db.add_pending_like(from_user_id, to_user_id)
    
    message_text = "Кто-то поставил суперлайк твоей анкете. 💌\nПоказать кто это был? 😮"
    
    from utils.keyboards import get_like_notification_keyboard
    
    await context.bot.send_message(
        chat_id=to_user_id,
        text=message_text,
        reply_markup=get_like_notification_keyboard()
    )

async def check_more_likes(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Проверяет есть ли еще непрочитанные лайки"""
    pending_likes = db.get_pending_likes(user_id)
    
    if pending_likes:
        # Показываем следующее уведомление
        await send_like_notification(context, pending_likes[0]['from_user_id'], user_id)
        return True
    
    return False

__all__ = [
    'send_like_notification',
    'send_superlike_notification',
    'check_more_likes'
]
##[file content end]