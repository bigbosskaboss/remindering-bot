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


#Состояния конечных автоматов
class Reminder(StatesGroup):
    check_time = State()
    alarm = State()


#Авторизация
bot = Bot(token='2115612018:AAEipk6w6QmIfE8-h4Mn9CN_Ae3GWgkZ7Yg')
dp = Dispatcher(bot, storage=MemoryStorage())


#Приветственное сообщение
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply('Привет, я бот, напиши мне что-нибудь!', reply_markup=get_start_keyboard())


# @dp.message_handler(commands=['help'])
# async def process_help_command(message: types.Message):
#     await bot.send_message(message.from_user.id, text='не ебу чем тебе помочь')


#Создаем начальную клавиатуру
def get_start_keyboard():
    start_keyboard = types.InlineKeyboardMarkup()
    button_select_time = types.InlineKeyboardButton('Выбрать время', callback_data='select')
    button_help = types.InlineKeyboardButton('Помощь', callback_data='help')
    button_settings = types.InlineKeyboardButton('Настройки', callback_data='settings')
    start_keyboard.add(button_help, button_select_time, button_settings)
    return start_keyboard



global NOTE_TIME
NOTE_TIME = '23:59'


@dp.message_handler(content_types='text', state=Reminder.check_time)
async def answer(message: types.Message, state:FSMContext):
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
    aioschedule.every().day.at(NOTE_TIME).do(notification, chat_id)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(3)


async def scheduler():
    print('proverka')
    # time.sleep()
    # aioschedule.every().day.at(NOTE_TIME).do(notification)
    # while True:
    #     await aioschedule.run_pending()
    #     await asyncio.sleep(3)


async def on_startup(x):
    asyncio.create_task(scheduler())

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


async def notification(chat_id):
    print('все ок, работаем')
    await bot.send_message(chat_id=chat_id, text='Привет, я твое напоминание', reply_markup=postpone_keyboard())


@dp.callback_query_handler(lambda c: c.data)
async def callback_time(call: types.CallbackQuery):
    if call.data == 'select':
        await call.message.reply("Введите время в формате HH:MM")
        await Reminder.check_time.set()
    if call.data == 'game':
        print('the game is starting')


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)


