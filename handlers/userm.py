from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
import rasterio
import requests
import os
from dotenv import load_dotenv
from text_messages.bot_mes import *
from storage.json_work import get_user, upsert_user
# === Настройка ===
router = Router()
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

dataset = rasterio.open(pollution_path)

geo_button = KeyboardButton(text=GPS_BUTMESSAGE, request_location=True)
gps_keyboard = ReplyKeyboardMarkup(keyboard=[[geo_button]], resize_keyboard=True)


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(START_MESSAGE, reply_markup=gps_keyboard)

@router.message(Command("help"))
async def help(message: Message):
    await message.answer(HELP_MESSAGE)

@router.message(Command("gps"))
async def send_gps_button(message: Message):
    await message.answer(GPS_MESSAGE, reply_markup=gps_keyboard)

@router.message(F.location)
async def handle_location(message: Message):
    lat = message.location.latitude
    lon = message.location.longitude
    user_id = str(message.from_user.id)
    upsert_user(user_id, {"lat": lat, "lon": lon})

    await message.answer(GPS_SUCCESS, reply_markup=ReplyKeyboardRemove())

@router.message(Command("weather"))
async def weather(message: Message):
    user_id = str(message.from_user.id)
    user = get_user(user_id)
    if not user:
        await message.answer(WEATHER_ERROR)
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
        await message.answer(weather_message, parse_mode="HTML")
    else:
        await message.answer(APIWEATHER_ERROR)

@router.message(Command("sky"))
async def sky(message: Message):
    user_id = str(message.from_user.id)
    user = get_user(user_id)
    if not user:
        await message.answer(WEATHER_ERROR)
        return

    lat = user.get("lat")
    lon = user.get("lon")

    # --- Функции ---
    def azimuth_to_direction(azimuth: float) -> str:
        directions = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
        index = round(azimuth / 45) % 8
        return directions[index]

    def brightness_description(magnitude: float) -> str:
        if magnitude < 0:
            return "очень ярко"
        elif 0 <= magnitude <= 3:
            return "ярко"
        elif 3 < magnitude <= 6:
            return "заметно"
        else:
            return "тускло, не видно"

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

    url = f"https://api.visibleplanets.dev/v3?latitude={lat}&longitude={lon}&aboveHorizon=true"
    response = requests.get(url)

    if response.status_code != 200:
        await message.answer(WEATHER_ERROR + pollution_message)
        return

    planets_data = response.json()
    bodies = planets_data.get("data", [])

    if not bodies:
        await message.answer(NO_PL + pollution_message)
        return

    sun = next((body for body in bodies if body.get("name") == "Sun"), None)

    if sun and sun.get("altitude", 0) > 0:
        direction = azimuth_to_direction(sun["azimuth"])
        msg = (
            "☀ Сейчас день — звёзд не видно.\n"
            f"Солнце на высоте {sun['altitude']:.1f}°, направление: {direction}."
            + pollution_message
        )
        await message.answer(msg)
        return

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
    await message.answer(msg)
