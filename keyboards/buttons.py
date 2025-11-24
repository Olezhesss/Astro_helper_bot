from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from text_messages.bot_mes import *
from storage.json_work import *

# === Кнопки ===
weather_button = KeyboardButton(text=but_weather)
sky_button = KeyboardButton(text=but_sky)
gps_button = KeyboardButton(text=but_gps, request_location=True)
facts_button = KeyboardButton(text=but_facts)
learn_button = KeyboardButton(text=but_learn)
apod_button = KeyboardButton(text=apod)

# === Основная клавиатура ===
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [weather_button],
        [sky_button],
        [facts_button],
        [gps_button],
        [learn_button],
        [apod_button]
    ],
    resize_keyboard=True
)
