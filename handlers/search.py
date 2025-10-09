##[file name]: handlers/search.py
from telegram import Update, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters, CallbackQueryHandler
from config import VIEWING_PROFILES, MAIN_MENU, SUPERLIKE_MESSAGE, db
from utils.keyboards import get_main_menu_keyboard, get_viewing_keyboard, get_superlike_cancel_keyboard, get_premium_offer_keyboard
from handlers.notifications import send_like_notification, send_superlike_notification

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало поиска анкет с фильтрацией по полу и городу"""
    user_id = update.message.from_user.id
    
    # Проверяем, есть ли у пользователя заполненный профиль
    user_profile = db.get_profile(user_id)
    if not user_profile:
        await update.message.reply_text(
            "❌ Сначала заполните свою анкету через 'Моя анкета📄'",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    print(f"🔍 ПОИСК: Пользователь {user_id} запустил поиск")
    
    # Активируем профиль для поиска
    db.update_profile_status(user_id, True)
    
    # Проверяем непрочитанные суперлайки
    unread_superlikes = db.get_unread_superlikes(user_id)
    if unread_superlikes:
        await show_unread_superlikes(update, context, unread_superlikes)
    
    await update.message.reply_text(
        "🔍 Ищу подходящую анкету для тебя 👀",
        reply_markup=get_viewing_keyboard()  # Меняем на клавиатуру просмотра
    )
    
    # Получаем фильтры для поиска
    target_gender = get_target_gender(user_profile.get('gender'))
    user_city = user_profile.get('city')
    
    print(f"🔍 ФИЛЬТРЫ: город='{user_city}', пол='{target_gender}'")
    
    # Ищем анкету с фильтрами
    filters = {}
    if user_city:
        filters['city'] = user_city
    if target_gender:
        filters['gender'] = target_gender
    
    print(f"🔍 ВЫПОЛНЯЕМ ПОИСК: exclude_user_id={user_id}, filters={filters}")
    
    random_profile = db.get_random_profile(exclude_user_id=user_id, filters=filters)
    
    if not random_profile:
        print("🔍 ПЕРВЫЙ ПОИСК: Не найдено, пробуем без фильтра по городу")
        # Пробуем без фильтра по городу
        if 'city' in filters:
            filters_no_city = filters.copy()
            filters_no_city.pop('city')
            random_profile = db.get_random_profile(exclude_user_id=user_id, filters=filters_no_city)
    
    if not random_profile:
        print("🔍 ВТОРОЙ ПОИСК: Не найдено, пробуем вообще без фильтров")
        # Пробуем вообще без фильтров
        random_profile = db.get_random_profile(exclude_user_id=user_id)
    
    if not random_profile:
        print("🔍 ПОИСК: Анкет не найдено вообще")
        await update.message.reply_text(
            "😔 Пока нет подходящих анкет для показа.\n\n"
            "Попробуй позже или пригласи друзей!",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    print(f"🔍 ПОИСК: Найден профиль - {random_profile.get('name')}")
    
    # Сохраняем текущий просматриваемый профиль в контексте
    context.user_data['current_viewing_profile'] = random_profile
    context.user_data['current_viewing_user_id'] = random_profile['user_id']
    context.user_data['search_filters'] = filters
    
    print(f"🔍 ПЕРЕХОДИМ К ПОКАЗУ ПРОФИЛЯ")
    
    # Показываем найденную анкету
    await show_random_profile(update, context, random_profile)
    
    print(f"🔍 ПОИСК ЗАВЕРШЕН УСПЕШНО")
    
    return VIEWING_PROFILES

def get_target_gender(user_gender: str) -> str:
    """Определяет противоположный пол для поиска с учетом смайликов 🥷 и 💅"""
    if not user_gender:
        return ""
    
    print(f"🎯 ОПРЕДЕЛЕНИЕ ПОЛА: Входные данные: '{user_gender}'")
    
    user_gender_lower = user_gender.lower()
    
    # Все возможные варианты для парня (включая смайлик 🥷)
    if any(word in user_gender_lower for word in ["парень", "парен", "мужск", "мальчик", "🥷"]):
        result = "Я девушка 💅"
        print(f"🎯 ОПРЕДЕЛЕНИЕ ПОЛА: Пользователь парень -> ищем: '{result}'")
        return result
    
    # Все возможные варианты для девушки (включая смайлик 💅)  
    elif any(word in user_gender_lower for word in ["девушка", "девушку", "женск", "девочка", "💅"]):
        result = "Я парень 🥷"
        print(f"🎯 ОПРЕДЕЛЕНИЕ ПОЛА: Пользователь девушка -> ищем: '{result}'")
        return result
    
    print(f"🎯 ОПРЕДЕЛЕНИЕ ПОЛА: Не удалось определить пол из '{user_gender}'")
    return ""

async def show_unread_superlikes(update: Update, context: ContextTypes.DEFAULT_TYPE, superlikes: list):
    """Показывает непрочитанные суперлайки"""
    for superlike in superlikes:
        from_user_id = superlike['from_user_id']
        from_user_profile = db.get_profile(from_user_id)
        
        if from_user_profile:
            message = (
                f"⭐ ВАМ СУПЕРЛАЙК! ⭐\n\n"
                f"От: {from_user_profile.get('name')}, {from_user_profile.get('age')}, {from_user_profile.get('city')}\n"
                f"💌 Сообщение: {superlike['message']}\n\n"
                f"💕 Кто-то очень заинтересован в знакомстве с тобой!"
            )
            
            # Отправляем фото если есть
            if from_user_profile.get('photos'):
                caption = f"{from_user_profile.get('city')}, {from_user_profile.get('age')}, {from_user_profile.get('name')}"
                media_group = []
                for i, photo_id in enumerate(from_user_profile['photos']):
                    if i == 0:
                        media_group.append(InputMediaPhoto(media=photo_id, caption=caption))
                    else:
                        media_group.append(InputMediaPhoto(media=photo_id))
                
                await update.message.reply_media_group(media=media_group)
            
            await update.message.reply_text(message)
            
            # Отмечаем суперлайк как прочитанный
            db.mark_superlike_read(from_user_id, update.message.from_user.id)

async def show_random_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, profile):
    """Показывает случайную анкету"""
    print(f"🎯 ПОКАЗ ПРОФИЛЯ: Начинаем показ профиля {profile.get('name')}")
    
    # Получаем статистику профиля
    stats = db.get_user_stats(profile['user_id'])
    
    # Формируем описание с статистикой
    caption = (
        f"🏙 {profile.get('city', 'Город')}, {profile.get('age', 'Возраст')}, {profile.get('name', 'Имя')}\n"
        f"❤️ Получено лайков: {stats['likes_received']}\n\n"
        f"{profile.get('description', 'Описание')}"
    )
    
    print(f"🎯 ОПИСАНИЕ ПРОФИЛЯ: {caption}")
    
    # Отправляем фотографии профиля
    if profile.get('photos'):
        print("🎯 Отправляем фото профиля")
        media_group = []
        for i, photo_id in enumerate(profile['photos']):
            if i == 0:
                media_group.append(InputMediaPhoto(media=photo_id, caption=caption))
            else:
                media_group.append(InputMediaPhoto(media=photo_id))
        
        try:
            await update.message.reply_media_group(media=media_group)
            print("🎯 Фото отправлены успешно")
        except Exception as e:
            print(f"❌ Ошибка отправки фото: {e}")
            # Если фото не отправились, отправляем текстовое описание
            await update.message.reply_text(caption)
    else:
        print("🎯 Отправляем текстовый профиль (без фото)")
        await update.message.reply_text(caption)
    
    # Отправляем подсказку о действиях
    await update.message.reply_text(
        "Выберите действие с анкетой:",
        reply_markup=get_viewing_keyboard()
    )
    
    print("🎯 ПРОФИЛЬ УСПЕШНО ПОКАЗАН")

async def handle_viewing_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий с анкетой через клавиатуру"""
    user_id = update.message.from_user.id
    text = update.message.text
    current_profile_id = context.user_data.get('current_viewing_user_id')
    
    print(f"🎯 ОБРАБОТКА ДЕЙСТВИЯ: {text} для профиля {current_profile_id}")
    
    if text == "❤️ Лайк":
        await handle_like_message(update, context, user_id, current_profile_id)
        
    elif text == "👎 Дизлайк":
        await handle_dislike_message(update, context)
        
    elif text == "⭐ Суперлайк":
        await handle_superlike_message_menu(update, context, user_id, current_profile_id)
        
    elif text == "🚫 Пожаловаться":
        await handle_report_message(update, context, user_id, current_profile_id)
        
    elif text == "⏹️ Стоп":
        await handle_stop_search_message(update, context)
        
    elif text == "💫 Premium":
        await handle_premium_message(update, context)
        
    else:
        await update.message.reply_text(
            "Используйте кнопки для взаимодействия с анкетой",
            reply_markup=get_viewing_keyboard()
        )

async def handle_like_message(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, profile_id: int):
    """Обработка лайка через сообщение"""
    if profile_id:
        # Добавляем лайк в базу
        db.add_like(user_id, profile_id)
        
        # Отправляем уведомление пользователю
        await send_like_notification(context, user_id, profile_id)
        
        await update.message.reply_text("❤️ Вы поставили лайк!", reply_markup=get_viewing_keyboard())
    
    # Показываем следующую анкету
    await show_next_profile(update, context)

async def handle_dislike_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка дизлайка через сообщение"""
    await update.message.reply_text("👎 Дизлайк поставлен", reply_markup=get_viewing_keyboard())
    await show_next_profile(update, context)

async def handle_superlike_message_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, profile_id: int):
    """Обработка суперлайка через меню"""
    # Проверяем премиум-статус
    if not db.is_premium(user_id):
        print(f"🎯 У ПОЛЬЗОВАТЕЛЯ {user_id} НЕТ ПРЕМИУМА ДЛЯ СУПЕРЛАЙКА")
        premium_text = (
            "К сожалению, данная функция доступна только пользователям с премиум статусом. Ты можешь купить нашу подписку и получить неограниченное количество суперлайков! 💌\n\n"
            "Суперлайк💌 - уникальная функция, позволяющая тебе не только оценить анкету, но и отправить сообщение напрямую её владельцу.\n"
            "Очень удобно и оперативно, не правда ли? ☺️"
        )
        
        from utils.keyboards import get_premium_offer_keyboard
        await update.message.reply_text(premium_text, reply_markup=get_premium_offer_keyboard())
        return
    
    print(f"🎯 У ПОЛЬЗОВАТЕЛЯ {user_id} ЕСТЬ ПРЕМИУМ - ОБРАБОТКА СУПЕРЛАЙКА")
    
    if profile_id:
        # Сохраняем данные для суперлайка
        context.user_data['pending_superlike'] = {
            'to_user_id': profile_id
        }
        
        await update.message.reply_text(
            "⭐ СУПЕРЛАЙК! ⭐\n\n"
            "Пожалуйста, введи свое сообщение, которое ты бы хотел отправить данному пользователю! 💌\n\n"
            "💌 Пример: 'Привет! Мне очень понравилась твоя анкета, давай познакомимся?'\n\n"
            "❌ Для отмены введите /cancel",
            reply_markup=get_viewing_keyboard()
        )
        
        return SUPERLIKE_MESSAGE

async def handle_superlike_message_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщения для суперлайка"""
    user_id = update.message.from_user.id
    message_text = update.message.text
    
    pending_superlike = context.user_data.get('pending_superlike')
    
    if pending_superlike and len(message_text) <= 500:
        to_user_id = pending_superlike['to_user_id']
        
        # Отправляем суперлайк
        db.add_superlike(user_id, to_user_id, message_text)
        
        # Отправляем уведомление
        await send_superlike_notification(context, user_id, to_user_id, message_text)
        
        await update.message.reply_text(
            "⭐ Суперлайк отправлен! Сообщение доставлено пользователю.",
            reply_markup=get_viewing_keyboard()
        )
        
        # Показываем следующую анкету
        await show_next_profile(update, context)
        return VIEWING_PROFILES
    else:
        await update.message.reply_text(
            "❌ Сообщение слишком длинное (макс. 500 символов). Попробуй короче:",
            reply_markup=get_viewing_keyboard()
        )
        return SUPERLIKE_MESSAGE

async def handle_report_message(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, profile_id: int):
    """Обработка жалобы через сообщение"""
    if profile_id:
        db.add_report(user_id, profile_id, "Жалоба из просмотра анкет")
    
    await update.message.reply_text(
        "Жалоба на анкету была успешно отправлена! ✅\n"
        "Спасибо, что стараетесь ради нашего комьюнити! Мы проверим анкету и предпримем все возможные меры по удалению потенциально неприемлемого контента!",
        reply_markup=get_main_menu_keyboard()
    )
    
    return MAIN_MENU

async def handle_stop_search_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Остановка поиска через сообщение"""
    user_id = update.message.from_user.id
    
    print(f"⏹️ ОСТАНОВКА ПОИСКА: пользователь {user_id}")
    
    # Деактивируем профиль для поиска
    db.update_profile_status(user_id, False)
    
    # Очищаем данные поиска из контекста
    if 'current_viewing_profile' in context.user_data:
        del context.user_data['current_viewing_profile']
    if 'current_viewing_user_id' in context.user_data:
        del context.user_data['current_viewing_user_id']
    if 'search_filters' in context.user_data:
        del context.user_data['search_filters']
    
    await update.message.reply_text(
        "⏹️ Поиск остановлен. Ваша анкета больше не показывается другим пользователям.\n\n"
        "Чтобы возобновить поиск, нажмите 'Начать общение📝'",
        reply_markup=get_main_menu_keyboard()
    )
    
    # Явно возвращаем состояние MAIN_MENU
    return MAIN_MENU

async def handle_premium_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ информации о премиуме"""
    premium_text = (
        "Кажется ты заинтересовался нашей премиум-подпиской! Давай я немного расскажу тебе о функциях, которые ты с ней получишь:\n\n"
        "⭐️ - Взаимные лайки на анкеты тех, кому ты понравился! ❤️‍🔥\n"
        "⭐️ - Возможность ставить суперлайки! 💌\n"
        "⭐️ - Статус «Premium💫» на твоей анкете!"
    )
    
    from utils.keyboards import get_premium_purchase_keyboard
    await update.message.reply_text(premium_text, reply_markup=get_premium_purchase_keyboard())

async def show_next_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает следующую анкету"""
    print("🔍 ПОИСК СЛЕДУЮЩЕЙ АНКЕТЫ")
    
    user_id = update.effective_user.id
    
    # Получаем фильтры из контекста
    filters = context.user_data.get('search_filters', {})
    
    print(f"🔍 ФИЛЬТРЫ ДЛЯ ПОИСКА: {filters}")
    
    # Ищем следующую анкету
    random_profile = db.get_random_profile(exclude_user_id=user_id, filters=filters)
    
    if not random_profile:
        print("🔍 НЕ НАЙДЕНО С ФИЛЬТРАМИ, ПРОБУЕМ БЕЗ ГОРОДА")
        # Пробуем без фильтра по городу
        if 'city' in filters:
            filters_no_city = filters.copy()
            filters_no_city.pop('city')
            random_profile = db.get_random_profile(exclude_user_id=user_id, filters=filters_no_city)
    
    if not random_profile:
        print("🔍 НЕ НАЙДЕНО ВООБЩЕ")
        await update.message.reply_text(
            "😔 Больше нет анкет для показа.\n\n"
            "Попробуй позже или пригласи друзей!",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    print(f"🔍 НАЙДЕНА АНКЕТА: {random_profile.get('name')}")
    
    # Сохраняем текущий просматриваемый профиль
    context.user_data['current_viewing_profile'] = random_profile
    context.user_data['current_viewing_user_id'] = random_profile['user_id']
    
    # Показываем найденную анкету
    await show_random_profile(update, context, random_profile)
    
    return VIEWING_PROFILES

# Обработчики для поиска
search_handlers = [
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_viewing_actions),  # Обработка действий в состоянии VIEWING_PROFILES
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_superlike_message_input)  # Сообщение для суперлайка
]

# Экспорт для импорта в main.py
__all__ = [
    'start_search',
    'show_random_profile', 
    'handle_superlike_message_input',
    'show_next_profile',
    'search_handlers'
]
##[file content end]