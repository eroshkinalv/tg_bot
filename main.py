import emoji
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
import os
from dotenv import load_dotenv
from src.bot_db import create_table, update_quiz_index, get_quiz_index, get_answer_count, get_answer_top, get_user_name
from src.quiz_data import quiz_data

load_dotenv(override=True)


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Замените "YOUR_BOT_TOKEN" на токен, который вы получили от BotFather
API_TOKEN = os.getenv('BOT_TOKEN')

# Объект бота
bot = Bot(token=API_TOKEN)

# Диспетчер
dp = Dispatcher()


def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()
    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else option)
        )
    builder.adjust(1)
    return builder.as_markup()


@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):

    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']
    answer_count = await get_answer_count(callback.from_user.id)
    user_name = await get_user_name(callback.from_user.id)
    await callback.message.answer(
        emoji.emojize(":green_circle:") + f"{quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    answer_count += 1
    await update_quiz_index(callback.from_user.id, user_name, current_question_index, answer_count)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        if answer_count == 1:
            await callback.message.answer(f"Вы ответили верно на {answer_count} вопрос.")
        elif answer_count in [2, 3, 4]:
            await callback.message.answer(f"Вы ответили верно на {answer_count} вопроса.")
        else:
            await callback.message.answer(f"Вы ответили верно на {answer_count} вопросов.")

        await callback.message.answer(emoji.emojize(":trophy:") + "Топ 10 игроков:")
        answer_top = await get_answer_top()
        top_ten = ""
        for item in answer_top:
            top_ten += f"{item[0]} - {item[1]} \n"
        await callback.message.answer(top_ten)


@dp.callback_query(F.data != "right_answer")
async def wrong_answer(callback: types.CallbackQuery):

    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)
    answer_count = await get_answer_count(callback.from_user.id)
    user_name = await get_user_name(callback.from_user.id)
    await callback.message.answer(emoji.emojize(":red_circle:") + f"{callback.data}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, user_name, current_question_index, answer_count)
    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        if answer_count == 1:
            await callback.message.answer(f"Вы ответили верно на {answer_count} вопрос.")
        elif answer_count in [2, 3, 4]:
            await callback.message.answer(f"Вы ответили верно на {answer_count} вопроса.")
        else:
            await callback.message.answer(f"Вы ответили верно на {answer_count} вопросов.")

        await callback.message.answer(emoji.emojize(":trophy:") + "Топ 10 игроков:")
        answer_top = await get_answer_top()
        top_ten = ""
        for item in answer_top:
            top_ten += f"{item[0]} - {item[1]} \n"
        await callback.message.answer(top_ten)


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Привет! Я бот для проведения квиза. Введите /quiz, чтобы начать.",
                         reply_markup=builder.as_markup(resize_keyboard=True))


async def get_question(message, user_id):

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


async def new_quiz(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    if user_name is None:
        user_name = message.from_user.first_name
    current_question_index = 0
    await update_quiz_index(user_id, user_name, current_question_index, answer=0)
    await get_question(message, user_id)


# Хэндлер на команду /quiz
@dp.message(F.text == "Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer("Давайте начнем квиз!")
    await new_quiz(message)


# Запуск процесса поллинга новых апдейтов
async def main():

    # Запускаем создание таблицы базы данных
    await create_table()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
