# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = "7753129964:AAG2xwh6wnHbIzAZUGxESZm9DxlrSegBaoI"

# Состояния ConversationHandler
(
    START, CITY, AGE, GENDER, NAME, DESCRIPTION, PHOTOS, MAIN_MENU,
    EDIT_PROFILE, EDIT_DESCRIPTION, EDIT_PHOTOS, VIEWING_PROFILES,
    SUPERLIKE_MESSAGE
) = range(13)

# Временное хранилище данных
user_data = {}

# Импортируем JSON базу данных
from database.manager import db