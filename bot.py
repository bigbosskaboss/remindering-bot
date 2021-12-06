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
    aioschedule.every().day.at(NOTE_TIME).do(notification, chat_id)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(3)


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
    await bot.send_message(chat_id=chat_id, text='Привет, время начать игру', reply_markup=postpone_keyboard())
    await Reminder.next()


@dp.callback_query_handler(lambda c: c.data)
async def callback_time(call: types.CallbackQuery):
    if call.data == 'select':
        await call.message.reply("Введите время в формате HH:MM")
        await Reminder.check_time.set()


@dp.callback_query_handler(lambda c: c.data, state=Reminder.alarm)
async def callback_remind(call: types.CallbackQuery):
    if call.data == 'game':
        await call.message.reply("The game is started")
    if call.data == '1':
        hour = call.data
        aioschedule.every().day.at(convert(hour)).do(postpone_note, call.message.chat.id, call.data)
        await call.message.reply('Отложил игру на час')
    if call.data == '2':
        hour = call.data
        aioschedule.every().day.at(convert(hour)).do(postpone_note, call.message.chat.id, call.data)
        await call.message.reply('Отложил игру на 2 часа')
    if call.data == '4':
        hour = call.data
        aioschedule.every().day.at(convert(hour)).do(postpone_note, call.message.chat.id, call.data)
        await call.message.reply('Отложил игру на 4 часа')
    if call.data == '8':
        hour = call.data
        aioschedule.every().day.at(convert(hour)).do(postpone_note, call.message.chat.id, call.data)
        await call.message.reply('Отложил игру на 8 часов')
    if call.data == '24':
        await call.message.reply('Отложил игру на завтра')


async def postpone_note(chat_id, hour):
    await bot.send_message(chat_id=chat_id, text='Время пришло! Давай начинать! ')


def convert(hour):
    now = datetime.datetime.now()
    now_to_str = now.strftime('%H:%M')
    now_to_str = now_to_str.split(':')
    itogo = str(int(now_to_str[0])) + ':' + str(int(now_to_str[1]) + int(hour))
    return itogo


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)