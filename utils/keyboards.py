#[file name]: utils/keyboards.py
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
def get_main_menu_keyboard():
    return ReplyKeyboardMarkup([
        ["Моя анкета📄", "Начать общение📝"],
        ["Купить Premium💫", "Служба поддержки⚙️"]
    ], resize_keyboard=True)

# Меню во время просмотра анкет (заменяет главное меню)
def get_viewing_keyboard():
    return ReplyKeyboardMarkup([
        ["❤️ Лайк", "👎 Дизлайк", "⭐ Суперлайк"],
        ["🚫 Пожаловаться", "⏹️ Стоп", "💫 Premium"]
    ], resize_keyboard=True)

# Меню редактирования профиля
def get_edit_profile_keyboard():
    return ReplyKeyboardMarkup([
        ["✏️ Изменить текст анкеты", "🖼 Изменить фото"],
        ["🔄 Заполнить анкету заново", "🔙 Назад"]
    ], resize_keyboard=True)

# Клавиатура для принятия условий
def get_accept_terms_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Политика конфиденциальности", 
                             url="https://docs.google.com/document/your-privacy-policy")],
        [InlineKeyboardButton("📝 Пользовательское соглашение", 
                             url="https://docs.google.com/document/your-terms-of-service")],
        [InlineKeyboardButton("✅ ПРИНЯТЬ УСЛОВИЯ", callback_data="accept_terms")]
    ])

# Клавиатура выбора города
def get_city_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏙️ Москва", callback_data="city_moscow")],
        [InlineKeyboardButton("🏙️ Санкт-Петербург", callback_data="city_spb")],
        [InlineKeyboardButton("🏙️ Казань", callback_data="city_kazan")]
    ])

# Клавиатура выбора пола
def get_gender_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Я парень 🥷", callback_data="gender_male")],
        [InlineKeyboardButton("Я девушка 💅", callback_data="gender_female")]
    ])

# Клавиатура для завершения загрузку фото
def get_photos_complete_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Завершить загрузку фото", callback_data="photos_complete")]
    ])

# Клавиатура для возврата в меню редактирования
def get_back_to_edit_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад к редактированию", callback_data="back_to_edit")]
    ])

# Клавиатура для отмены суперлайка
def get_superlike_cancel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отменить суперлайк", callback_data="superlike_cancel")]
    ])

# Клавиатура для покупки премиума
def get_premium_payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить Premium", callback_data="premium_payment")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ])

# 🔥 КЛАВИАТУРЫ ДЛЯ УВЕДОМЛЕНИЙ О ЛАЙКАХ:

# Уведомление о лайке
def get_like_notification_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Показать", callback_data="show_liker")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ])

# После показа профиля лайкнувшего
def get_after_show_liker_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❤️‍🔥", callback_data="mutual_like")],
        [InlineKeyboardButton("💔", callback_data="back_to_main")]
    ])

# Предложение премиума
def get_premium_offer_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Купить Premium💫", callback_data="buy_premium")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ])

# Подтверждение покупки премиума
def get_premium_purchase_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Получить", callback_data="get_premium")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ])

# Клавиатура для суперлайка сообщения
def get_superlike_message_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Посмотреть сообщение💌", callback_data="view_superlike_message")],
        [InlineKeyboardButton("Не хочу", callback_data="hide_superlike_buttons")]
    ])
##[file content end]