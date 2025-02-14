import asyncio
import logging
import sys, os, json, hashlib
from dotenv import find_dotenv, load_dotenv
from parser import get_news

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.markdown import hbold, hlink

load_dotenv(find_dotenv())

dp = Dispatcher()
SEEN_NEWS_FILE = "seen_news.json"

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Загружаем просмотренные новости
def load_seen_news():
    if os.path.exists(SEEN_NEWS_FILE):
        try:
            with open(SEEN_NEWS_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                return {user: set(news) for user, news in data.items()} if isinstance(data, dict) else {}
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Ошибка загрузки seen_news.json: {e}")
    return {}


# Сохраняем просмотренные новости
def save_seen_news(seen_news):
    with open(SEEN_NEWS_FILE, "w", encoding="utf-8") as file:
        json.dump({user: list(news) for user, news in seen_news.items()}, file, indent=4, ensure_ascii=False)


# Функция для создания уникального хэша новости
def generate_news_id(text, link):
    hash_obj = hashlib.sha256(f"{text}_{link}".encode("utf-8"))
    return hash_obj.hexdigest()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    start_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Узнать новости ✅')]], resize_keyboard=True)
    await message.answer("Приветствую в нашем боте новостей 🗞️!\nНажмите на кнопку, чтобы узнать последние мировые новости ⬇️",
                         reply_markup=start_kb)


@dp.message(F.text == 'Узнать новости ✅')
async def send_news(message: Message) -> None:
    user_id = str(message.from_user.id)
    await message.answer("Пожалуйста, подождите...")

    # Удаляем старый файл перед парсингом
    if os.path.exists("news.json"):
        os.remove("news.json")

    # Обновляем новости
    logging.info("Запуск парсинга новостей...")
    get_news()
    logging.info("Парсинг завершен.")

    # Загружаем новости ПОСЛЕ парсинга
    if not os.path.exists("news.json"):
        logging.error("Файл news.json не был создан после парсинга!")
        await message.answer("Ошибка при загрузке новостей. Попробуйте позже.")
        return

    with open("news.json", encoding="utf-8") as file:
        data = json.load(file)

    if not data:
        logging.warning("Файл news.json пуст.")
        await message.answer("Новостей пока нет 😢")
        return

    logging.info(f"Загружено {len(data)} новостей.")

    seen_news = load_seen_news()
    user_seen = seen_news.get(user_id, set())

    new_news = []
    for item in data:
        news_text = item.get("text", "Без заголовка")
        news_link = item.get("src", "#")
        news_id = generate_news_id(news_text, news_link)

        # Логируем каждую новость
        logging.info(f"Проверка новости: {news_text[:30]}... (ID: {news_id})")

        if news_id in user_seen:
            logging.info("Новость уже отправлена пользователю.")
            continue

        text = hbold(news_text)
        link = hlink("Читать статью", news_link)
        img = item.get("img")

        card = f"{text}\n{link}\n{img}" if img else f"{text}\n{link}"

        await message.answer(card)
        await asyncio.sleep(2)

        new_news.append(news_id)

    if new_news:
        seen_news[user_id] = user_seen.union(set(new_news))
        save_seen_news(seen_news)
        logging.info(f"Сохранены {len(new_news)} новых новостей для пользователя {user_id}.")
    else:
        logging.info(f"Нет новых новостей для пользователя {user_id}.")
        await message.answer("Вы уже видели все последние новости 😊")


async def main() -> None:
    bot = Bot(token=os.getenv("TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
