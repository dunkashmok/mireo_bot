
import re
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, MessageHandler, filters, CallbackQueryHandler
from config import EDIT_PROFILE, EDIT_DESCRIPTION, EDIT_PHOTOS, MAIN_MENU, START
from config import user_data, db
from utils.keyboards import (
    get_edit_profile_keyboard, 
    get_main_menu_keyboard, 
    get_back_to_edit_keyboard,
    get_photos_complete_keyboard
)
from handlers.start import start

async def show_profile_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ анкеты пользователя из сообщения"""
    return await show_profile(update, context, is_callback=False)

async def show_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ анкеты пользователя из callback"""
    return await show_profile(update, context, is_callback=True)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback: bool = False):
    """Показ анкеты пользователя"""
    if is_callback:
        user_id = update.callback_query.from_user.id
        chat_id = update.callback_query.message.chat_id
        await update.callback_query.answer()
    else:
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
    
    # Пробуем получить данные из временного хранилища
    if user_id not in user_data:
        # Если нет во временном хранилище, пробуем из базы данных
        user_profile = db.get_profile(user_id)
        if user_profile:
            user_data[user_id] = user_profile
        else:
            if is_callback:
                await context.bot.send_message(chat_id, "❌ Сначала заполните анкету через /start")
            else:
                await update.message.reply_text("❌ Сначала заполните анкету через /start")
            return MAIN_MENU
    
    user = user_data[user_id]
    
    # Отправляем фотографии
    if user.get('photos'):
        caption = f"🏙 {user.get('city', 'Город')}, {user.get('age', 'Возраст')}, {user.get('name', 'Имя')}\n\n{user.get('description', 'Описание')}"
        
        media_group = []
        for i, photo_id in enumerate(user['photos']):
            if i == 0:
                media_group.append(InputMediaPhoto(media=photo_id, caption=caption))
            else:
                media_group.append(InputMediaPhoto(media=photo_id))
        
        await context.bot.send_media_group(chat_id=chat_id, media=media_group)
        
        # Показываем меню редактирования
        await context.bot.send_message(
            chat_id=chat_id,
            text="🛠 Что хочешь изменить в анкете?",
            reply_markup=get_edit_profile_keyboard()
        )
    else:
        # Если фото нет, отправляем только текст
        profile_text = (
            f"🏙 {user.get('city', 'Город')}, {user.get('age', 'Возраст')}, {user.get('name', 'Имя')}\n\n"
            f"{user.get('description', 'Описание')}\n\n"
            f"🛠 Что хочешь изменить в анкете?"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=profile_text,
            reply_markup=get_edit_profile_keyboard()
        )
    
    return EDIT_PROFILE

async def handle_edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка меню редактирования профиля"""
    user_id = update.message.from_user.id
    text = update.message.text
    
    if text == "✏️ Изменить текст анкеты":
        await update.message.reply_text(
            "📝 Введи новый текст для своей анкеты:\n\n"
            "Расскажи о своих предпочтениях: кто ты, кого ищешь и какие совместные занятия тебе интересны.",
            reply_markup=get_back_to_edit_keyboard()
        )
        return EDIT_DESCRIPTION
        
    elif text == "🖼 Изменить фото":
        # Убеждаемся что user_data[user_id] существует
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['photos'] = []  # Очищаем фото
        
        await update.message.reply_text(
            "🖼 Старые фото удалены. Теперь пришли мне новые фото (от 3 до 5 штук)\n\n"
            "Когда загрузишь достаточно фото, нажми кнопку:",
            reply_markup=get_photos_complete_keyboard()
        )
        return EDIT_PHOTOS
        
    elif text == "🔄 Заполнить анкету заново":
        user_data[user_id] = {}
        await update.message.reply_text("🔄 Начинаем заполнение анкеты заново!")
        return await start(update, context)
        
    elif text == "🔙 Назад":
        await update.message.reply_text(
            "Возвращаемся в главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU

async def edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактирование описания"""
    user_id = update.message.from_user.id
    new_description = update.message.text
    
    # Проверки
    if re.search(r'[a-zA-Z]', new_description):
        await update.message.reply_text(
            "❌ В твоем сообщении содержатся недопустимые символы. "
            "Используй только русские буквы. Пожалуйста, отправь описание еще раз:"
        )
        return EDIT_DESCRIPTION
    
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    if url_pattern.search(new_description):
        await update.message.reply_text(
            "❌ В твоем сообщении содержится ссылка. "
            "Пожалуйста, отправь описание без ссылок еще раз:"
        )
        return EDIT_DESCRIPTION
    
    # Сохраняем новое описание
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['description'] = new_description
    
    # Сохраняем в базу данных
    db.save_profile(user_id, user_data[user_id])
    
    await update.message.reply_text("✅ Текст анкеты успешно обновлен!")
    
    # Возвращаем к просмотру профиля
    return await show_profile_message(update, context)

async def edit_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактирование фотографий"""
    user_id = update.message.from_user.id
    
    # Убеждаемся что user_data[user_id] существует
    if user_id not in user_data:
        user_data[user_id] = {}
    
    if 'photos' not in user_data[user_id]:
        user_data[user_id]['photos'] = []
    
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id
        user_data[user_id]['photos'].append(photo_id)
        
        photo_count = len(user_data[user_id]['photos'])
        
        if photo_count > 5:
            await update.message.reply_text(
                "❌ Вы прислали больше 5 фотографий!\n\n"
                "К сожалению я не могу принять больше 5 фото. "
                "Пожалуйста, пришлите от 3 до 5 фотографий заново.",
                reply_markup=get_photos_complete_keyboard()
            )
            user_data[user_id]['photos'] = []
            return EDIT_PHOTOS
        
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
    
    return EDIT_PHOTOS

async def finish_edit_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение редактирования фото через инлайн-кнопку"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    if 'photos' not in user_data[user_id]:
        user_data[user_id]['photos'] = []
    
    photo_count = len(user_data[user_id]['photos'])
    
    if photo_count < 3:
        await query.edit_message_text(
            f"❌ Добавлено только {photo_count} фото. Нужно минимум 3. Продолжай загружать фото:",
            reply_markup=get_photos_complete_keyboard()
        )
        return EDIT_PHOTOS
    elif photo_count > 5:
        await query.edit_message_text(
            "❌ Вы прислали больше 5 фотографий!\n\n"
            "К сожалению я не могу принять больше 5 фото. "
            "Пожалуйста, пришлите от 3 до 5 фотографий заново.",
            reply_markup=get_photos_complete_keyboard()
        )
        user_data[user_id]['photos'] = []
        return EDIT_PHOTOS
    else:
        # Сохраняем в базу данных
        db.save_profile(user_id, user_data[user_id])
        
        await query.edit_message_text("✅ Фотографии успешно обновлены!")
        
        # Показываем обновленный профиль
        await context.bot.send_message(
            chat_id=chat_id,
            text="Ваш обновленный профиль:"
        )
        
        # Создаем простой update для показа профиля
        from telegram import Message, Chat, User
        fake_message = Message(
            message_id=query.message.message_id + 1,
            date=query.message.date,
            chat=Chat(id=chat_id, type="private"),
            from_user=User(id=user_id, first_name="User", is_bot=False),
            text="show_profile"
        )
        fake_update = Update(update_id=update.update_id, message=fake_message)
        
        return await show_profile_message(fake_update, context)

async def handle_back_to_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Назад к редактированию'"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    await query.edit_message_text("Возвращаемся к редактированию профиля...")
    
    # Создаем простой update для показа профиля
    from telegram import Message, Chat, User
    fake_message = Message(
        message_id=query.message.message_id + 1,
        date=query.message.date,
        chat=Chat(id=chat_id, type="private"),
        from_user=User(id=user_id, first_name="User", is_bot=False),
        text="show_profile"
    )
    fake_update = Update(update_id=update.update_id, message=fake_message)
    
    return await show_profile_message(fake_update, context)

# Обработчики для редактирования профиля
profile_handlers = [
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_profile),  # EDIT_PROFILE
    MessageHandler(filters.TEXT & ~filters.COMMAND, edit_description),     # EDIT_DESCRIPTION
    MessageHandler(filters.PHOTO, edit_photos),                           # EDIT_PHOTOS (фото)
    CallbackQueryHandler(finish_edit_photos, pattern='^photos_complete$'), # EDIT_PHOTOS (инлайн-кнопка)
    CallbackQueryHandler(handle_back_to_edit, pattern='^back_to_edit$')   # Назад к редактированию
]
