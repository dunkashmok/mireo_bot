import re
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from config import CITY, AGE, GENDER, NAME, DESCRIPTION, PHOTOS, MAIN_MENU, db
from config import user_data
from utils.keyboards import get_gender_keyboard, get_main_menu_keyboard, get_city_keyboard, get_photos_complete_keyboard

async def select_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора города через инлайн-кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("city_"):
        user_id = query.from_user.id
        city_map = {
            "city_moscow": "Москва",
            "city_spb": "Санкт-Петербург", 
            "city_kazan": "Казань"
        }
        city = city_map.get(query.data, "Москва")
        user_data[user_id]['city'] = city
        
        await query.edit_message_text(f"🏙️ Выбран город: {city}\n\nСколько тебе лет? (отправь число)")
        return AGE

async def check_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка возраста"""
    user_id = update.message.from_user.id
    age_text = update.message.text
    
    try:
        age = int(age_text)
        
        if age < 18:
            await update.message.reply_text(
                "❌ К сожалению, работа нашего бота доступна только для пользователей старше 18 лет\n\n"
                "Регистрация сброшена. Нажми /start чтобы начать заново, когда тебе исполнится 18 лет."
            )
            if user_id in user_data:
                del user_data[user_id]
            return ConversationHandler.END
        elif age > 80:
            await update.message.reply_text(
                "❌ К сожалению, работа нашего бота доступна только для пользователей до 80 лет\n\n"
                "Регистрация сброшена. Нажми /start чтобы начать заново, когда помолодеешь"
            )
            if user_id in user_data:
                del user_data[user_id]
            return ConversationHandler.END
        else:
            user_data[user_id]['age'] = age
            
            # Используем инлайн-кнопки для выбора пола
            await update.message.reply_text(
                "Отлично! Теперь выбери свой пол:",
                reply_markup=get_gender_keyboard()
            )
            return GENDER
            
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректный возраст (число):")
        return AGE

async def select_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора пола через инлайн-кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("gender_"):
        user_id = query.from_user.id
        # ИСПРАВЛЕННЫЙ ФОРМАТ - с сохранением смайликов 🥷 и 💅
        gender_map = {
            "gender_male": "Я парень 🥷",
            "gender_female": "Я девушка 💅"
        }
        gender = gender_map.get(query.data, "Я парень 🥷")
        user_data[user_id]['gender'] = gender
        
        await query.edit_message_text(f"✅ Пол выбран: {gender}\n\nКак тебя зовут? (только русские буквы)")
        return NAME

async def check_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка имени"""
    user_id = update.message.from_user.id
    name = update.message.text
    
    if re.match(r'^[а-яА-ЯёЁ\s\-]+$', name):
        user_data[user_id]['name'] = name
        
        await update.message.reply_text(
            "📝 Чтобы мы могли найти идеальную компанию для тебя, расскажи о своих предпочтениях:\n"
            "• Кто ты\n• Кого ищешь\n• Какие совместные занятия тебе интересны"
        )
        return DESCRIPTION
    else:
        await update.message.reply_text(
            "❌ В твоем сообщении содержатся недопустимые символы. "
            "Используй только русские буквы. Пожалуйста, отправь имя еще раз:"
        )
        return NAME

async def check_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка описания"""
    user_id = update.message.from_user.id
    description = update.message.text
    
    # Проверка на иностранные буквы
    if re.search(r'[a-zA-Z]', description):
        await update.message.reply_text(
            "❌ В твоем сообщении содержатся недопустимые символы. "
            "Используй только русские буквы. Пожалуйста, отправь описание еще раз:"
        )
        return DESCRIPTION
    
    # Проверка на ссылки
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    if url_pattern.search(description):
        await update.message.reply_text(
            "❌ В твоем сообщении содержится ссылка. "
            "Пожалуйста, отправь описание без ссылок еще раз:"
        )
        return DESCRIPTION
    
    user_data[user_id]['description'] = description
    
    # Используем инлайн-кнопку для перехода к загрузке фото
    await update.message.reply_text(
        "✅ Описание сохранено!\n\n"
        "📸 Теперь пришли мне фото (от 3 до 5 штук)\n\n"
        "Можно отправлять по одному или несколько сразу. "
        "Когда загрузишь достаточно фото, нажми кнопку ниже:",
        reply_markup=get_photos_complete_keyboard()
    )
    
    return PHOTOS

async def handle_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фотографий"""
    user_id = update.message.from_user.id
    
    if 'photos' not in user_data[user_id]:
        user_data[user_id]['photos'] = []
    
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id
        user_data[user_id]['photos'].append(photo_id)
        
        photo_count = len(user_data[user_id]['photos'])
        
        # Проверка на превышение лимита
        if photo_count > 5:
            await update.message.reply_text(
                "❌ Вы прислали больше 5 фотографий!\n\n"
                "К сожалению я не могу принять больше 5 фото. "
                "Пожалуйста, пришлите от 3 до 5 фотографий заново."
            )
            user_data[user_id]['photos'] = []
            await update.message.reply_text(
                "📸 Теперь пришли мне фото (от 3 до 5 штук)",
                reply_markup=get_photos_complete_keyboard()
            )
            return PHOTOS
        
        # Информация о количестве с инлайн-кнопкой
        if photo_count < 3:
            await update.message.reply_text(
                f"📸 Загружено фото: {photo_count}/5 (нужно еще {3 - photo_count})",
                reply_markup=get_photos_complete_keyboard()
            )
        else:
            await update.message.reply_text(
                f"✅ Загружено фото: {photo_count}/5\n\nНажми кнопку чтобы завершить:",
                reply_markup=get_photos_complete_keyboard()
            )
    
    return PHOTOS

async def check_photos_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение загрузки фото через инлайн-кнопку"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "photos_complete":
        user_id = query.from_user.id
        
        if 'photos' not in user_data[user_id]:
            user_data[user_id]['photos'] = []
        
        photo_count = len(user_data[user_id]['photos'])
        
        if photo_count < 3:
            await query.edit_message_text(
                f"❌ Добавлено только {photo_count} фото. Нужно минимум 3. Продолжай загружать фото:",
                reply_markup=get_photos_complete_keyboard()
            )
            return PHOTOS
        elif photo_count > 5:
            await query.edit_message_text(
                "❌ Вы прислали больше 5 фотографий!\n\n"
                "К сожалению я не могу принять больше 5 фото. "
                "Пожалуйста, пришлите от 3 до 5 фотографий заново.",
                reply_markup=get_photos_complete_keyboard()
            )
            user_data[user_id]['photos'] = []
            return PHOTOS
        else:
            # Сохраняем профиль в базу данных
            if user_id in user_data:
                db.save_profile(user_id, user_data[user_id])
            
            await query.edit_message_text("🎉 Отлично! Регистрация завершена!")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Теперь ты можешь посмотреть свою анкету или начать общение с другими пользователями.",
                reply_markup=get_main_menu_keyboard()
            )
            
            return MAIN_MENU

# Обновленный список обработчиков с CallbackQueryHandler
registration_handlers = [
    CallbackQueryHandler(select_city, pattern='^city_'),  # CITY (инлайн-кнопки)
    MessageHandler(filters.TEXT & ~filters.COMMAND, check_age),    # AGE
    CallbackQueryHandler(select_gender, pattern='^gender_'), # GENDER (инлайн-кнопки)
    MessageHandler(filters.TEXT & ~filters.COMMAND, check_name),   # NAME
    MessageHandler(filters.TEXT & ~filters.COMMAND, check_description), # DESCRIPTION
    MessageHandler(filters.PHOTO, handle_photos),                  # PHOTOS (фото)
    CallbackQueryHandler(check_photos_complete, pattern='^photos_complete$') # PHOTOS (инлайн-кнопка)
]