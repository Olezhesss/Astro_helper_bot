from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from text_messages.bot_mes import *

import requests
import json
import os
from dotenv import load_dotenv

router = Router()
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

geo_button = KeyboardButton(text=GPS_BUTMESSAGE, request_location=True)
gps_keyboard = ReplyKeyboardMarkup(keyboard=[[geo_button]], resize_keyboard=True)


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(START_MESSAGE, reply_markup=gps_keyboard)


@router.message(Command("help"))
async def help(message: Message):
    await message.answer(HELP_MESSAGE)

@router.message(Command("7221"))
async def help(message: Message):
    await message.answer(stto)

@router.message(Command("gps"))
async def send_gps_button(message: Message):
    await message.answer(GPS_MESSAGE, reply_markup=gps_keyboard)


@router.message(F.location)
async def handle_location(message: Message):
    lat = message.location.latitude
    lon = message.location.longitude
    user_id = str(message.from_user.id)

    data = {}
    if os.path.exists("users.json"):
        with open("users.json", "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    data = {}

    # Обновление координат
    data[user_id] = {"lat": lat, "lon": lon}

    # Сохранение обратно
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await message.answer(GPS_SUCCESS, reply_markup=ReplyKeyboardRemove())

@router.message(Command("weather"))
async def weather(message: Message):
    user_id = str(message.from_user.id)
    
    # Проверка, есть ли файл с координатами
    if not os.path.exists("users.json"):
        await message.answer(WEATHER_ERROR)
        return

    # Чтение координат пользователя
    with open("users.json", "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    
    if user_id not in data:
        await message.answer(WEATHER_ERROR)
        return
    
    lat = data[user_id]["lat"]
    lon = data[user_id]["lon"]

    # Запрос к OpenWeatherMap
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)

    # Преобразуем ответ в JSON
    weather_data = response.json()

    # Проверка успешного запроса
    if weather_data.get("cod") == 200:
        temp = weather_data["main"]["temp"]
        feels_like = weather_data["main"]["feels_like"]
        humidity = weather_data["main"]["humidity"]
        wind_speed = weather_data["wind"]["speed"]
        description = weather_data["weather"][0]["description"].capitalize()
        city_name = weather_data.get("name", "Ваш город")

        # Формируем красивое сообщение
        weather_message = (
            f"🌆 <b>{city_name}</b>\n"
            f"🌡 Температура: {temp}°C (ощущается как {feels_like}°C)\n"
            f"☁ Погода: {description}\n"
            f"💧 Влажность: {humidity}%\n"
            f"💨 Ветер: {wind_speed} м/с"
        )

        await message.answer(weather_message, parse_mode="HTML")
    else:
        await message.answer(APIWEATHER_ERROR)
