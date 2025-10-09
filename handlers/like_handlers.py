##[file name]: handlers/like_handlers.py

from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, CallbackQueryHandler
from config import MAIN_MENU, db
from utils.keyboards import get_main_menu_keyboard, get_premium_purchase_keyboard, get_after_show_liker_keyboard, get_premium_offer_keyboard, get_premium_payment_keyboard
from handlers.notifications import check_more_likes

async def show_liker_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, from_user_id: int, to_user_id: int, like_type: str = 'like'):
    """Показывает профиль пользователя, который поставил лайк"""
    query = update.callback_query
    await query.answer()
    
    print(f"🎯 ПОКАЗ ПРОФИЛЯ ЛАЙКНУВШЕГО: от {from_user_id} для {to_user_id}")
    
    liker_profile = db.get_profile(from_user_id)
    if not liker_profile:
        await query.edit_message_text("❌ Профиль не найден")
        return
    
    # Формируем описание профиля
    caption = f"🏙 {liker_profile.get('city', 'Город')}, {liker_profile.get('age', 'Возраст')}, {liker_profile.get('name', 'Имя')}"
    
    if db.is_premium(from_user_id):
        caption += " 💫 Premium"
    
    caption += f"\n\n{liker_profile.get('description', 'Описание')}"
    
    # Сохраняем информацию для взаимного лайка
    context.user_data['current_liker'] = {
        'user_id': from_user_id,
        'name': liker_profile.get('name', 'Пользователь')
    }
    
    # Отправляем фото профиля
    if liker_profile.get('photos'):
        media_group = []
        for i, photo_id in enumerate(liker_profile['photos']):
            if i == 0:
                media_group.append(InputMediaPhoto(media=photo_id, caption=caption))
            else:
                media_group.append(InputMediaPhoto(media=photo_id))
        
        await context.bot.send_media_group(chat_id=to_user_id, media=media_group)
        
        # Показываем кнопки для взаимного действия
        if db.is_premium(to_user_id):
            await context.bot.send_message(
                chat_id=to_user_id,
                text="Выберите действие:",
                reply_markup=get_after_show_liker_keyboard()
            )
        else:
            premium_text = (
                "К сожалению, данная функция доступна только пользователям с премиум статусом. "
                "Ты можешь купить нашу подписку и взаимно оценивать анкеты тех, кто тебя лайкнул!❤️\n\n"
                "❤️‍🔥 - Данная функция позволит тебе ответить взаимностью на лайк и уведомить об этом пользователя!\n"
                "Ты получишь возможность общаться с ним напрямую! 😉"
            )
            
            await context.bot.send_message(
                chat_id=to_user_id,
                text=premium_text,
                reply_markup=get_premium_offer_keyboard()
            )
    else:
        await context.bot.send_message(
            chat_id=to_user_id,
            text=caption,
            reply_markup=get_after_show_liker_keyboard()
        )
    
    # Удаляем исходное сообщение с уведомлением
    await query.delete_message()

async def handle_mutual_like(update: Update, context: ContextTypes.DEFAULT_TYPE, user1_id: int, user2_id: int):
    """Обрабатывает взаимный лайк"""
    query = update.callback_query
    await query.answer()
    
    print(f"🎯 ВЗАИМНЫЙ ЛАЙК: между {user1_id} и {user2_id}")
    
    # Добавляем взаимный лайк в базу
    db.add_mutual_like(user1_id, user2_id)
    
    # Удаляем pending лайк
    db.remove_pending_like(user2_id, user1_id)
    
    # Получаем профили обоих пользователей
    user1_profile = db.get_profile(user1_id)
    user2_profile = db.get_profile(user2_id)
    
    if user1_profile and user2_profile:
        # Уведомляем первого пользователя
        user1_message = f"Есть контакт! Скорее начинай общаться 🙌 [{user2_profile.get('name')}](tg://user?id={user2_id})"
        await context.bot.send_message(chat_id=user1_id, text=user1_message, parse_mode='Markdown')
        
        # Уведомляем второго пользователя  
        user2_message = f"Кажется кто-то из тех, кого ты лайкнул заинтересовался тобой! Может, самое время сделать первый шаг🤔 [{user1_profile.get('name')}](tg://user?id={user1_id})"
        await context.bot.send_message(chat_id=user2_id, text=user2_message, parse_mode='Markdown')
    
    await query.edit_message_text("❤️‍🔥 Вы ответили взаимностью!")

async def handle_show_liker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Показать' - показывает профиль того, кто поставил лайк"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    print(f"🎯 ПОКАЗ ПРОФИЛЯ ЛАЙКНУВШЕГО: пользователь {user_id}")
    
    # Получаем непрочитанные лайки
    pending_likes = db.get_pending_likes(user_id)
    if not pending_likes:
        await query.edit_message_text("❌ Лайки не найдены")
        return
    
    # Берем первый непрочитанный лайк
    like_data = pending_likes[0]
    from_user_id = like_data['from_user_id']
    
    # Отмечаем как прочитанный
    db.mark_like_read(from_user_id, user_id)
    
    # Вызываем функцию показа профиля
    await show_liker_profile(update, context, from_user_id, user_id)

async def handle_mutual_like_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка взаимного лайка ❤️‍🔥"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    liker_data = context.user_data.get('current_liker')
    
    print(f"🎯 ВЗАИМНЫЙ ЛАЙК: пользователь {user_id}")
    
    if not liker_data:
        await query.edit_message_text("❌ Информация о лайке не найдена")
        return
    
    from_user_id = liker_data['user_id']
    
    # Вызываем функцию взаимного лайка
    await handle_mutual_like(update, context, user_id, from_user_id)

async def handle_back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    print(f"🎯 ВОЗВРАТ В ГЛАВНОЕ МЕНЮ: пользователь {user_id}")
    
    # Проверяем есть ли еще непрочитанные лайки
    has_more_likes = await check_more_likes(context, user_id)
    
    if not has_more_likes:
        print("🎯 НЕТ НЕПРОЧИТАННЫХ ЛАЙКОВ - ПОКАЗЫВАЕМ ГЛАВНОЕ МЕНЮ")
        # Если лайков больше нет - показываем главное меню
        await query.edit_message_text(
            "Возвращаемся в главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
    
    return MAIN_MENU

async def handle_buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка премиума из уведомления"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    print(f"🎯 ПОКАЗ ПРЕДЛОЖЕНИЯ ПРЕМИУМА: пользователь {user_id}")
    
    premium_text = (
        "💫 Премиум подписка Mireo\n\n"
        "Откройте все возможности знакомств:\n\n"
        "⭐️ - Взаимные лайки на анкеты тех, кому ты понравился! ❤️‍🔥\n"
        "⭐️ - Возможность ставить суперлайки с сообщениями! 💌\n"
        "⭐️ - Статус «Premium💫» на вашей анкете\n"
        "⭐️ - Приоритет в поиске и рекомендациях\n\n"
        "Стоимость: 299 руб./месяц"
    )
    
    await query.edit_message_text(
        premium_text,
        reply_markup=get_premium_payment_keyboard()
    )

async def handle_premium_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка оплаты премиума"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    print(f"🎯 ОПЛАТА ПРЕМИУМА: пользователь {user_id}")
    
    # Здесь будет интеграция с ЮКассой
    # Пока просто активируем премиум для тестирования
    db.set_premium(user_id, days=30)
    
    await query.edit_message_text(
        "✅ Премиум подписка активирована! Теперь ты обладаешь всеми функциями Premium💫.\n\n"
        "Спасибо за покупку!",
        reply_markup=get_main_menu_keyboard()
    )
    
    return MAIN_MENU

async def handle_get_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение премиума (старая функция для совместимости)"""
    return await handle_premium_payment(update, context)

# Обработчики для лайков и премиума
like_handlers = [
    CallbackQueryHandler(handle_show_liker, pattern='^show_liker$'),
    CallbackQueryHandler(handle_mutual_like_callback, pattern='^mutual_like$'),
    CallbackQueryHandler(handle_back_to_main, pattern='^back_to_main$'),
    CallbackQueryHandler(handle_buy_premium, pattern='^buy_premium$'),
    CallbackQueryHandler(handle_premium_payment, pattern='^premium_payment$'),
    CallbackQueryHandler(handle_get_premium, pattern='^get_premium$')
]

# Экспорт для импорта в main.py
__all__ = [
    'show_liker_profile',
    'handle_mutual_like',
    'handle_show_liker',
    'handle_mutual_like_callback', 
    'handle_back_to_main',
    'handle_buy_premium',
    'handle_premium_payment',
    'handle_get_premium',
    'like_handlers'
]
##[file content end]