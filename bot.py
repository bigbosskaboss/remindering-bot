import aiogram
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import time
import datetime
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio
import aioschedule
import psycopg2
from crontab import CronTab


global NOTE_TIME
NOTE_TIME = '23:59'


def db_connect(chat_id):
    connection = psycopg2.connect(dbname='postgres',
                                  user='postgres',
                                  password='123',
                                  host='localhost')
    cursor = connection.cursor()
    # cursor.execute('''TRUNCATE TABLE REMINDER''')
    # cursor.execute(f'''ALTER TABLE REMINDER ADD PRIMARY KEY (user_id)''')
    # connection.commit()
    cursor.execute(f'''INSERT
    INTO
    REMINDER(user_id, relevant_time)
    VALUES('{chat_id}', '{NOTE_TIME}')
    ON
    CONFLICT(user_id)
    DO
    UPDATE
    SET
    relevant_time = EXCLUDED.relevant_time; ''')
    cursor.execute('''SELECT * FROM REMINDER''')
    rows = cursor.fetchall()
    print(rows)
    connection.commit()
    connection.close()


def take_time_db(chat_id):
    connection = psycopg2.connect(dbname='postgres',
                                  user='postgres',
                                  password='123',
                                  host='localhost')
    cursor = connection.cursor()
    cursor.execute(f'''SELECT relevant_time FROM REMINDER WHERE user_id='{chat_id}';''')
    # cursor.execute('''SELECT * FROM REMINDER''')
    rows = cursor.fetchall()
    rows = str(rows)
    rows = rows.split("'")
    NOTE_TIME = rows[1]
    connection.commit()
    connection.close()
    return NOTE_TIME


# cursor.execute('''CREATE TABLE REMINDER
#      (user_id VARCHAR(100),
#      relevant_time VARCHAR(5));''')
# connection.commit()
# cursor.execute('''INSERT INTO REMINDER (user_id, relevant_time) VALUES('@petrov', '2015') ''')
# cursor.execute('''SELECT * FROM REMINDER''')
# rows = cursor.fetchall()
# print(rows)


# Состояния конечных автоматов
class Reminder(StatesGroup):
    check_time = State()
    alarm = State()
    PREcheck = State()


# Авторизация
bot = Bot(token='2115612018:AAEipk6w6QmIfE8-h4Mn9CN_Ae3GWgkZ7Yg')
dp = Dispatcher(bot, storage=MemoryStorage())


# async def check_users():
#     connection = psycopg2.connect(dbname='postgres',
#                                   user='postgres',
#                                   password='123',
#                                   host='localhost')
#     cursor = connection.cursor()
#     # cursor.execute('''TRUNCATE TABLE REMINDER''')
#     cursor.execute('''SELECT * FROM REMINDER''')
#     raws = cursor.fetchall()
#     for raw in raws:
#         raw = str(raw)
#         raw = raw.split("'")
#         # print(raw[1])
#         # global TIM
#         # global WHO
#         TIM = raw[3]
#         WHO = raw[1]


    #     # aioschedule.every().day.at(TIM).do(notification2)
    # print(dict)
    # while True:
    #     await aioschedule.run_pending()
    #     await asyncio.sleep(3)
    # connection.commit
    # connection.close()


# Приветственное сообщение
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply('Привет, я бот, напиши мне что-нибудь!', reply_markup=get_start_keyboard())


# Создаем начальную клавиатуру
def get_start_keyboard():
    start_keyboard = types.InlineKeyboardMarkup()
    button_select_time = types.InlineKeyboardButton('Выбрать время', callback_data='select')
    button_help = types.InlineKeyboardButton('Помощь', callback_data='help')
    button_settings = types.InlineKeyboardButton('Настройки', callback_data='settings')
    start_keyboard.add(button_help, button_select_time, button_settings)
    return start_keyboard


@dp.callback_query_handler(lambda c: c.data)
async def callback_time(call: types.CallbackQuery):
    if call.data == 'select':
        await call.message.reply("Введите время в формате HH:MM")
        await Reminder.check_time.set()


@dp.message_handler(content_types='text', state=Reminder.check_time)
async def answer(message: types.Message, state: FSMContext):
    try:
        time.strptime(message.text, '%H:%M')
        await message.reply('Отлично, мы запомним это время')
        # await Reminder.next
    except ValueError:
        await message.reply('Попробуйте еще раз')
        return
    global NOTE_TIME
    NOTE_TIME = message.text
    chat_id = message.chat.id
    db_connect(chat_id)
    NOTE_TIME = take_time_db(chat_id)
    aioschedule.every().day.at(NOTE_TIME).do(notification, chat_id)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(3)


async def notification(chat_id):
    await bot.send_message(chat_id=chat_id, text='Привет, время начать игру', reply_markup=postpone_keyboard())
    await Reminder.next()


def postpone_keyboard():
    alarm_keyboard = types.InlineKeyboardMarkup()
    button_game = types.InlineKeyboardButton('Начать игру', callback_data='game')
    button_postpone1 = types.InlineKeyboardButton('Отложить на 1 час', callback_data='1')
    button_postpone2 = types.InlineKeyboardButton('Отложить на 2 часа', callback_data='2')
    button_postpone4 = types.InlineKeyboardButton('Отложить на 4 час', callback_data='4')
    button_postpone8 = types.InlineKeyboardButton('Отложить на 8 час', callback_data='8')
    button_postpone24 = types.InlineKeyboardButton('Отложить на завтра', callback_data='24')
    alarm_keyboard.add(button_game, button_postpone1,
                       button_postpone2, button_postpone4,
                       button_postpone8, button_postpone24)
    return alarm_keyboard


@dp.callback_query_handler(lambda c: c.data, state=Reminder.alarm)
async def callback_remind(call: types.CallbackQuery, state: FSMContext):
    if call.data == 'game':
        await call.message.reply("The game is started")
    if call.data == '1':
        hour = call.data
        aioschedule.every().day.at(convert(hour)).do(postpone_note, call.message.chat.id)
        await call.message.reply('Отложил игру на час')
    if call.data == '2':
        hour = call.data
        aioschedule.every().day.at(convert(hour)).do(postpone_note, call.message.chat.id)
        await call.message.reply('Отложил игру на 2 часа')
    if call.data == '4':
        hour = call.data
        aioschedule.every().day.at(convert(hour)).do(postpone_note, call.message.chat.id)
        await call.message.reply('Отложил игру на 4 часа')
    if call.data == '8':
        hour = call.data
        aioschedule.every().day.at(convert(hour)).do(postpone_note, call.message.chat.id)
        await call.message.reply('Отложил игру на 8 часов')
    if call.data == '24':
        await call.message.reply('Отложил игру на завтра')


async def postpone_note(chat_id):
    await bot.send_message(chat_id=chat_id, text='Время пришло! Давай начинать! ')


def convert(hour):
    now = datetime.datetime.now()
    now_to_str = now.strftime('%H:%M')
    now_to_str = now_to_str.split(':')
    itogo = str(int(now_to_str[0])) + ':' + str(int(now_to_str[1]) + int(hour))
    return itogo


# myCron = CronTab(user=True)
# job = myCron.new(command='/Applications/anaconda3/bin/python3 /Users/kkabis/Desktop/lastsummerdance/cron.py')
# job.minute.every(1)
# myCron.write()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)
