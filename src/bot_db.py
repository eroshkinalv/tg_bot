import aiosqlite
import nest_asyncio
import os
from dotenv import load_dotenv

load_dotenv(override=True)
nest_asyncio.apply()


async def create_table():
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect(os.getenv("DB_NAME")) as db:
        # Выполняем SQL-запрос к базе данных
        # await db.execute( '''DROP TABLE IF EXISTS quiz_state''')
        await db.execute(
            """CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, 
            username VARCHAR(100), question_index INTEGER, correct_answers INTEGER)"""
        )
        # Сохраняем изменения
        await db.commit()


async def update_quiz_index(user_id, username, index, answer):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(os.getenv("DB_NAME")) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute(
            "INSERT OR REPLACE INTO quiz_state (user_id, username, question_index, correct_answers) "
            "VALUES (?, ?, ?, ?)",
            (user_id, username, index, answer),
        )
        # Сохраняем изменения
        await db.commit()


async def get_quiz_index(user_id):
    # Подключаемся к базе данных
    async with aiosqlite.connect(os.getenv("DB_NAME")) as db:
        # Получаем запись для заданного пользователя
        async with db.execute("SELECT question_index FROM quiz_state WHERE user_id = (?)", (user_id,)) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0


async def get_answer_count(user_id):
    # Подключаемся к базе данных
    async with aiosqlite.connect(os.getenv("DB_NAME")) as db:
        # Получаем запись для заданного пользователя
        async with db.execute("SELECT correct_answers FROM quiz_state WHERE user_id = (?)", (user_id,)) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0


async def get_answer_top():
    # Подключаемся к базе данных
    async with aiosqlite.connect(os.getenv("DB_NAME")) as db:
        # Получаем запись для заданного пользователя
        # async with db.execute('SELECT username FROM quiz_state ORDER BY correct_answers DESC LIMIT 10') as cursor:
        async with db.execute(
            "SELECT username, correct_answers FROM quiz_state ORDER BY correct_answers LIMIT 10"
        ) as cursor:

            # Возвращаем результат
            results = await cursor.fetchall()
            if results is not None:
                return results
            else:
                return 0


async def get_user_name(user_id):
    # Подключаемся к базе данных
    async with aiosqlite.connect(os.getenv("DB_NAME")) as db:
        # Получаем запись для заданного пользователя
        async with db.execute("SELECT username FROM quiz_state WHERE user_id = (?)", (user_id,)) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return "Неизвестный игрок"
