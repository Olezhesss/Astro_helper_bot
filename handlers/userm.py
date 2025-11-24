from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import Command
import rasterio
import requests
import os
import json
import random
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from text_messages.bot_mes import *
from keyboards.buttons import main_keyboard
from storage.json_work import *
import re
from deep_translator import GoogleTranslator

# === Настройка роутера и API ===
router = Router()
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

dataset = rasterio.open(pollution_path)

# === Функция отправки APOD ===
async def send_apod(message: types.Message):
    response = requests.get(APOD_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # Заголовок и картинка
    title = soup.find("b").text.strip() if soup.find("b") else "Astronomy Picture of the Day"
    img_tag = soup.find("img")
    img_url = APOD_DOMAIN + img_tag["src"] if img_tag else None

    # Текст между "Explanation:" и "Tomorrow's picture"
    full_text = soup.get_text(separator="\n")
    start, end = full_text.find("Explanation:"), full_text.find("Tomorrow's picture")
    explanation = " ".join(full_text[start:end].split()) if start != -1 and end != -1 else "Описание недоступно."

    # Перевод текста
    translated_title = GoogleTranslator(source='auto', target='ru').translate(title)
    translated_text = GoogleTranslator(source='auto', target='ru').translate(explanation)

    # Отправка пользователю
    if img_url:
        await message.answer_photo(img_url, caption=f"🌌 *{translated_title}*\n\n{translated_text}", parse_mode="Markdown")
    else:
        await message.answer(f"🌌 *{translated_title}*\n\n{translated_text}", parse_mode="Markdown")

# --- APOD команда и кнопка ---
@router.message(Command("apod"))
async def apod_command(message: Message):
    await send_apod(message)

@router.message(F.text == apod)
async def apod_button_handler(message: Message):
    await send_apod(message)

# === Кнопки погоды и фактов ===
@router.message(F.text == but_weather)
async def weather_button_handler(message: Message):
    await weather(message)

@router.message(lambda message: message.text == but_facts)
async def facts_button_handler(message: Message):
    fact = random.choice(space_facts)
    await message.answer(f"{fact}")

@router.message(F.text == but_sky)
async def sky_button_handler(message: Message):
    await sky(message)

# === Старт и помощь ===
@router.message(Command("start"))
async def start(message: Message):
    await message.answer(START_MESSAGE, reply_markup=main_keyboard)

@router.message(Command("help"))
async def help(message: Message):
    await message.answer(HELP_MESSAGE, reply_markup=main_keyboard)

# === GPS ===
@router.message(Command("gps"))
async def send_gps_button(message: Message):
    await message.answer(GPS_MESSAGE, reply_markup=main_keyboard)

@router.message(F.location)
async def handle_location(message: Message):
    lat = message.location.latitude
    lon = message.location.longitude
    user_id = str(message.from_user.id)
    upsert_user(user_id, {"lat": lat, "lon": lon})
    await message.answer(GPS_SUCCESS, reply_markup=main_keyboard)

# === Погода по координатам ===
@router.message(Command("weather"))
async def weather(message: Message):
    user_id = str(message.from_user.id)
    user = get_user(user_id)
    if not user:
        await message.answer(WEATHER_ERROR, reply_markup=main_keyboard)
        return

    lat = user.get("lat")
    lon = user.get("lon")

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)
    weather_data = response.json()

    if weather_data.get("cod") == 200:
        temp = weather_data["main"]["temp"]
        feels_like = weather_data["main"]["feels_like"]
        humidity = weather_data["main"]["humidity"]
        wind_speed = weather_data["wind"]["speed"]
        description = weather_data["weather"][0]["description"].capitalize()
        city_name = weather_data.get("name", "Ваш город")

        weather_message = (
            f"🌆 <b>{city_name}</b>\n"
            f"🌡 Температура: {temp}°C (ощущается как {feels_like}°C)\n"
            f"☁ Погода: {description}\n"
            f"💧 Влажность: {humidity}%\n"
            f"💨 Ветер: {wind_speed} м/с"
        )
        await message.answer(weather_message, parse_mode="HTML", reply_markup=main_keyboard)
    else:
        await message.answer(APIWEATHER_ERROR, reply_markup=main_keyboard)

# === Небо и планеты ===
@router.message(Command("sky"))
async def sky(message: Message):
    user_id = str(message.from_user.id)
    user = get_user(user_id)
    if not user:
        await message.answer(WEATHER_ERROR, reply_markup=main_keyboard)
        return

    lat = user.get("lat")
    lon = user.get("lon")

    # Направления по азимуту
    def azimuth_to_direction(azimuth: float) -> str:
        directions = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
        index = round(azimuth / 45) % 8
        return directions[index]

    # Яркость планет
    def brightness_description(magnitude: float) -> str:
        if magnitude < 0:
            return "очень ярко"
        elif 0 <= magnitude <= 3:
            return "ярко"
        elif 3 < magnitude <= 6:
            return "заметно"
        else:
            return "тускло, не видно"

    # Световое загрязнение
    def pollution_text(value):
        if value < 0.25:
            return best_p
        elif value < 1:
            return norm_p
        elif value < 5:
            return moderate_p
        elif value < 20:
            return big_p
        else:
            return huge_p

    try:
        for val in dataset.sample([(lon, lat)]):
            brightness = float(val[0])
    except Exception:
        brightness = None

    pollution_message = ""
    if brightness is not None:
        pollution_message = (
            f"\n\n💡 Уровень светового загрязнения: {brightness:.2f} нВт/см²/ср\n"
            f"{pollution_text(brightness)}"
        )

    # Получение планет
    url = f"https://api.visibleplanets.dev/v3?latitude={lat}&longitude={lon}&aboveHorizon=true"
    response = requests.get(url)
    if response.status_code != 200:
        await message.answer(WEATHER_ERROR + pollution_message, reply_markup=main_keyboard)
        return

    planets_data = response.json()
    bodies = planets_data.get("data", [])
    if not bodies:
        await message.answer(NO_PL + pollution_message, reply_markup=main_keyboard)
        return

    sun = next((body for body in bodies if body.get("name") == "Sun"), None)
    if sun and sun.get("altitude", 0) > 0:
        direction = azimuth_to_direction(sun["azimuth"])
        msg = (
            "☀ Сейчас день — звёзд не видно.\n"
            f"Солнце на высоте {sun['altitude']:.1f}°, направление: {direction}."
            + pollution_message
        )
        await message.answer(msg, reply_markup=main_keyboard)
        return

    # Информация о планетах
    msg = NOW__PL + "\n\n"
    for body in bodies:
        if body.get("name") == "Sun":
            continue
        name = planet_translation.get(body.get("name"), body.get("name"))
        constellation = constellation_translation.get(body.get("constellation"), body.get("constellation"))
        altitude = body.get("altitude")
        azimuth = body.get("azimuth")
        magnitude = body.get("magnitude")
        naked_eye = "да" if body.get("nakedEyeObject") else "нет"

        direction = azimuth_to_direction(azimuth)
        brightness = brightness_description(magnitude)
        note = ""
        if altitude < 5:
            note = " (низко, может быть не видно)"
        elif magnitude > 6:
            note = " (слишком тускло)"

        msg += (
            f"• {name} (созвездие {constellation})\n"
            f"  Направление: {direction}, высота {altitude:.1f}°{note}\n"
            f"  Видимость невооружённым глазом: {naked_eye}, яркость: {brightness}\n\n"
        )

    msg += pollution_message
    await message.answer(msg, reply_markup=main_keyboard)

# === Интересные факты ===
@router.message(Command("interest_facts"))
async def int_facts(message: Message):
    fact = random.choice(int_facts)
    await message.answer(f"{fact}")

# === Обучение / статьи ===
async def send_learn_articles(message: Message):
    if not LEARN_TOPICS:
        await message.answer("Пока нет доступных статей 🌌", reply_markup=main_keyboard)
        return

    for topic in LEARN_TOPICS:
        title = topic.get("title", "Без названия")
        url = topic.get("url", "#")
        text = f"📖 <b>{title}</b>\n🔗 {url}"
        await message.answer(text, parse_mode="HTML", reply_markup=main_keyboard)

@router.message(Command("learn"))
async def learn_c(message: Message):
    await send_learn_articles(message)

@router.message(F.text == but_learn)
async def learn_button_handler(message: Message):
    await send_learn_articles(message)
