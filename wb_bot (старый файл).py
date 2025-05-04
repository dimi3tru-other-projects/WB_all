import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', lambda x: '%.0f' % x)
import math
#from dateutil import parser
#import os, gc

import warnings
warnings.filterwarnings('ignore')
import matplotlib as mpl
import plotly.express as px
import seaborn as sns
mpl.style.use('seaborn') # так красивее
from pylab import *
#%matplotlib inline

import json
import requests
from datetime import date, datetime, timedelta

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
#import telebot

import nest_asyncio
nest_asyncio.apply()
from aiogram.dispatcher import filters
from aiogram.dispatcher.filters.state import State, StatesGroup
from html import *
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from openpyxl import Workbook

from IPython.core.display import display, HTML
display(HTML("<style>.container { width:98% ! important; }<style>"))

import dataframe_image as dfi








tg_bot_token = '...'
# wb_api = '...'
storage = MemoryStorage()
bot = Bot(token=tg_bot_token)
dp = Dispatcher(bot, storage=storage)


class FSMdata(StatesGroup):
    wb_api = State()


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# создаём клавиатуру
kb_1 = KeyboardButton('/Ввести_API_ключ\U0001F5A5')
kb_2 = KeyboardButton('/Заказы_по_товарам')
kb_3 = KeyboardButton('/Продажи_по_товарам')
kb_4 = KeyboardButton('/График_заказов_и_продаж')

kb_api = ReplyKeyboardMarkup(resize_keyboard=True)
kb_api.add(kb_1)
kb_main = ReplyKeyboardMarkup(resize_keyboard=True)
kb_main.row(kb_2, kb_3).row(kb_4)

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Достаём API продавца

df_user_api_excel = pd.read_excel("D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\df_user_api_excel.xlsx").astype(str)


@dp.message_handler(commands=['Ввести_API_ключ', 'start', 'api', 'Привет', 'привет'], state=None)
async def ask_API(message: types.Message):
    user_full_name = message.from_user.full_name
    user_id = message.from_user.id
    shape = df_user_api_excel[df_user_api_excel["user_id"] == str(user_id)]["user_api"].shape[0]

    if df_user_api_excel['user_id'].str.contains(str(message.from_user.id)).any():
        if requests.get(
                'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
                headers={'Authorization':
                             f'{df_user_api_excel[df_user_api_excel["user_id"] == str(user_id)]["user_api"].reset_index(drop=True)[shape - 1]}'}).status_code == 200:

            await bot.send_message(message.chat.id, f'Привет, ты уже авторизирован и можешь запрашивать статистику!',
                                   reply_markup=kb_main)
        else:
            await bot.send_message(message.chat.id,
                                   f'Привет, вижу, что ты уже пытался пройти авторизацию, но ввёл неверный '
                                   f'API ключ \U0001F614. Попробуй ввести его ещё раз, нажав на кнопку /Ввести_API_ключ\U0001F5A5, которая'
                                   f' находится внизу. \nAPI, который ты вводил до этого: '
                                   f'{df_user_api_excel[df_user_api_excel["user_id"] == str(user_id)].reset_index(drop=True)["user_api"][shape - 1]}',
                                   reply_markup=kb_api)
        # await message.delete_reply_markup()
    else:
        await FSMdata.wb_api.set()

        await bot.send_message(message.chat.id,
                               f'Привет, {user_full_name}, это бот статистики заказов и выкупов Wildberries!\n'
                               f'Введи сюда свой API ключ, который находится в настройках профиля на портале.\n'
                               f'Вот ссылка: https://seller.wildberries.ru/supplier-settings/access-to-new-api\n'
                               f'Здесь нажми "Создать новый ключ", выбери "Статистика" (так мы будем иметь доступ только к статистике, но не иметь доступа к созданию и редактированию карточек товара и т. д.)\n'
                               f'Теперь скопируй этот большой набор символов и отправь мне. Жду!', reply_markup=kb_api)
        # await message.answer(f'{user_full_name}, отправь в чат API ключ', reply_markup=kb_api)


@dp.message_handler(state=FSMdata.wb_api)
async def get_API(message: types.Message, state: FSMContext):
    global df_user_api_excel
    user_id = message.from_user.id
    if requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={'Authorization':
                         f'{df_user_api_excel[df_user_api_excel["user_id"] == str(user_id)]["user_api"].reset_index(drop=True)[shape - 1]}'}).status_code != 200:
        await bot.send_message(message.chat.id,
                               f'Мне кажется, что это не API ключ \U0001FAE0 \nПопробуй ещё раз. Следуй строго по инструкциями из первого сообщения.',
                               reply_markup=kb_api)
    else:
        async with state.proxy() as data:
            data['wb_api'] = message.text

        async with state.proxy() as data:
            user_id = str(message.from_user.id)
            user_api = "'".join(str(data)[61:].split("'")[:-1])
            df_user_api_excel.loc[len(df_user_api_excel)] = [user_id, user_api]
            writer = pd.ExcelWriter('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\df_user_api_excel.xlsx', engine='xlsxwriter')
            df_user_api_excel.drop_duplicates(subset=['user_id'], keep='last').to_excel(writer, sheet_name='Sheet1',
                                                                                        index=False)
            writer.save()
            await bot.send_message(message.chat.id,
                                   f'Твой ключ API: {df_user_api_excel["user_api"][0]}\nТеперь давай опробуем наш функционал.',
                                   reply_markup=kb_main)
        await state.finish()


##########   З   А   К   А   З   Ы      З   А   #########################################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
##########   З   А   К   А   З   Ы      З   А   #########################################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
##########   З   А   К   А   З   Ы      З   А   #########################################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


@dp.message_handler(commands="Заказы_по_товарам")
async def InlKB(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Заказы за сегодня", callback_data="Заказы_за_сегодня"))
    keyboard.add(types.InlineKeyboardButton(text="Заказы за вчера", callback_data="Заказы_за_вчера"))
    keyboard.add(types.InlineKeyboardButton(text="Заказы за эту неделю", callback_data="Заказы_за_эту_неделю"))
    keyboard.add(types.InlineKeyboardButton(text="Заказы за прошлую неделю", callback_data="Заказы_за_прошлую_неделю"))
    keyboard.add(types.InlineKeyboardButton(text="Заказы за этот месяц", callback_data="Заказы_за_этот_месяц"))
    keyboard.add(types.InlineKeyboardButton(text="Заказы за прошлый месяц", callback_data="Заказы_за_прошлый_месяц"))
    keyboard.add(
        types.InlineKeyboardButton(text="Заказы за последние 30 дней", callback_data="Заказы_за_последние_30_дней"))
    await message.answer("Выберите период, заказы по которому вы хотите узнать", reply_markup=keyboard)


@dp.callback_query_handler(text="Заказы_за_сегодня")
async def orders(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        today_orders = orders[(orders['date'] >= str(current_date)) & (orders['cancel_dt'] == '0001-01-01T00:00:00')]
        pivot_today_orders = pd.merge(
            pd.pivot_table(today_orders, values='PriceWithDiscount', index=['supplierArticle'],
                           aggfunc='count', margins=False).rename(columns={'PriceWithDiscount': 'qty'}),
            pd.pivot_table(today_orders,
                           values='PriceWithDiscount', index=['supplierArticle'], aggfunc='sum', margins=False),
            how="left",
            left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(by=['PriceWithDiscount'],
                                                                                             ascending=False,
                                                                                             na_position='first').reset_index(
            drop=True)
        df_styled = pivot_today_orders[['supplierArticle', 'qty', 'PriceWithDiscount']].head(50).style.set_precision(
            0).background_gradient(
            axis=0, gmap=pivot_today_orders['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Заказы за сегодня, общая сумма -"
                                                                 f" {int(round(sum(pivot_today_orders['PriceWithDiscount']), 0))} (с учётом СПП),"
                                                                 f" общее количество - {sum(pivot_today_orders['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме заказов.")
    except:
        await call.message.answer(f'\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(text="Заказы_за_вчера")
async def orders(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        yesterday_orders = orders[
            (orders['date'] < str(current_date)) & (orders['date'] >= str(current_date - timedelta(1))) &
            (orders['cancel_dt'] == '0001-01-01T00:00:00')]
        pivot_yesterday_orders = pd.merge(
            pd.pivot_table(yesterday_orders, values='PriceWithDiscount', index=['supplierArticle'],
                           aggfunc='count', margins=False).rename(columns={'PriceWithDiscount': 'qty'}),
            pd.pivot_table(yesterday_orders,
                           values='PriceWithDiscount', index=['supplierArticle'], aggfunc='sum', margins=False),
            how="left",
            left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(by=['PriceWithDiscount'],
                                                                                             ascending=False,
                                                                                             na_position='first').reset_index(
            drop=True)
        df_styled = pivot_yesterday_orders[['supplierArticle', 'qty', 'PriceWithDiscount']].head(
            50).style.set_precision(0).background_gradient(
            axis=0, gmap=pivot_yesterday_orders['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Заказы за вчера, общая сумма -"
                                                                 f" {int(round(sum(pivot_yesterday_orders['PriceWithDiscount']), 0))} (с учётом СПП),"
                                                                 f" общее количество - {sum(pivot_yesterday_orders['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме заказов.")
    except:
        await call.message.answer(f'\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(text="Заказы_за_эту_неделю")
async def orders(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        orders['week_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.isocalendar().week
        orders['year_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.year
        week_orders = orders[
            (orders['week_num'] >= max(orders['week_num'])) & (orders['year_num'] >= max(orders['year_num'])) & (
                        orders['cancel_dt'] == '0001-01-01T00:00:00')]
        pivot_week_orders = pd.merge(pd.pivot_table(week_orders, values='PriceWithDiscount', index=['supplierArticle'],
                                                    aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(week_orders,
                                                                  values='PriceWithDiscount', index=['supplierArticle'],
                                                                  aggfunc='sum', margins=False), how="left",
                                     left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(
            by=['PriceWithDiscount'],
            ascending=False, na_position='first').reset_index(drop=True)
        df_styled = pivot_week_orders[['supplierArticle', 'qty', 'PriceWithDiscount']].head(50).style.set_precision(
            0).background_gradient(
            axis=0, gmap=pivot_week_orders['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Заказы за эту неделю, общая сумма -"
                                                                 f" {int(round(sum(pivot_week_orders['PriceWithDiscount']), 0))} (с учётом СПП),"
                                                                 f" общее количество - {sum(pivot_week_orders['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме заказов.")
    except:
        await call.message.answer(f'\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(text="Заказы_за_прошлую_неделю")
async def orders(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        orders['week_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.isocalendar().week
        orders['year_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.year
        week_orders = orders[
            (orders['week_num'] == max(orders['week_num']) - 1) & (orders['year_num'] >= max(orders['year_num'])) & (
                        orders['cancel_dt'] == '0001-01-01T00:00:00')]
        pivot_past_week_orders = pd.merge(
            pd.pivot_table(week_orders, values='PriceWithDiscount', index=['supplierArticle'],
                           aggfunc='count', margins=False).rename(columns={'PriceWithDiscount': 'qty'}),
            pd.pivot_table(week_orders,
                           values='PriceWithDiscount', index=['supplierArticle'], aggfunc='sum', margins=False),
            how="left",
            left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(by=['PriceWithDiscount'],
                                                                                             ascending=False,
                                                                                             na_position='first').reset_index(
            drop=True)
        df_styled = pivot_past_week_orders[['supplierArticle', 'qty', 'PriceWithDiscount']].head(
            50).style.set_precision(0).background_gradient(
            axis=0, gmap=pivot_past_week_orders['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Заказы за прошлую неделю, общая сумма -"
                                                                 f" {int(round(sum(pivot_past_week_orders['PriceWithDiscount']), 0))} (с учётом СПП),"
                                                                 f" общее количество - {sum(pivot_past_week_orders['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме заказов.")
    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(text="Заказы_за_этот_месяц")
async def orders(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        orders['month_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.month
        orders['year_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.year
        current_month_orders = orders[
            (orders['month_num'] >= max(orders['month_num'])) & (orders['year_num'] >= max(orders['year_num'])) & (
                        orders['cancel_dt'] == '0001-01-01T00:00:00')]
        pivot_current_month_orders = pd.merge(pd.pivot_table(current_month_orders, values='PriceWithDiscount',
                                                             index=['supplierArticle'], aggfunc='count',
                                                             margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}),
                                              pd.pivot_table(current_month_orders, values='PriceWithDiscount',
                                                             index=['supplierArticle'], aggfunc='sum',
                                                             margins=False), how="left", left_on='supplierArticle',
                                              right_on='supplierArticle').reset_index().sort_values(
            by=['PriceWithDiscount'], ascending=False, na_position='first').reset_index(drop=True)
        df_styled = pivot_current_month_orders[['supplierArticle', 'qty', 'PriceWithDiscount']].head(
            50).style.set_precision(0).background_gradient(
            axis=0, gmap=pivot_current_month_orders['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Заказы за этот месяц, общая сумма -"
                                                                 f" {int(round(sum(pivot_current_month_orders['PriceWithDiscount']), 0))} (с учётом СПП),"
                                                                 f" общее количество - {sum(pivot_current_month_orders['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме заказов.")
    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(text="Заказы_за_прошлый_месяц")
async def orders(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        orders['month_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.month
        orders['year_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.year
        past_month_orders = orders[
            (orders['month_num'] == max(orders['month_num']) - 1) & (orders['year_num'] >= max(orders['year_num'])) & (
                        orders['cancel_dt'] == '0001-01-01T00:00:00')]
        pivot_past_month_orders = pd.merge(
            pd.pivot_table(past_month_orders, values='PriceWithDiscount', index=['supplierArticle'],
                           aggfunc='count', margins=False).rename(columns={'PriceWithDiscount': 'qty'}),
            pd.pivot_table(past_month_orders,
                           values='PriceWithDiscount', index=['supplierArticle'], aggfunc='sum', margins=False),
            how="left",
            left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(by=['PriceWithDiscount'],
                                                                                             ascending=False,
                                                                                             na_position='first').reset_index(
            drop=True)
        df_styled = pivot_past_month_orders[['supplierArticle', 'qty', 'PriceWithDiscount']].head(
            50).style.set_precision(0).background_gradient(
            axis=0, gmap=pivot_past_month_orders['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Заказы за прошлый месяц, общая сумма -"
                                                                 f" {int(round(sum(pivot_past_month_orders['PriceWithDiscount']), 0))} (с учётом СПП),"
                                                                 f" общее количество - {sum(pivot_past_month_orders['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме заказов.")
    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(text="Заказы_за_последние_30_дней")
async def orders(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        past_30_days_orders = orders[
            (orders['date'] >= str(current_date - timedelta(30))) & (orders['cancel_dt'] == '0001-01-01T00:00:00')]
        pivot_past_30_days_orders = pd.merge(
            pd.pivot_table(past_30_days_orders, values='PriceWithDiscount', index=['supplierArticle'],
                           aggfunc='count', margins=False).rename(columns={'PriceWithDiscount': 'qty'}),
            pd.pivot_table(past_30_days_orders,
                           values='PriceWithDiscount', index=['supplierArticle'], aggfunc='sum', margins=False),
            how="left",
            left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(by=['PriceWithDiscount'],
                                                                                             ascending=False,
                                                                                             na_position='first').reset_index(
            drop=True)
        df_styled = pivot_past_30_days_orders[['supplierArticle', 'qty', 'PriceWithDiscount']].head(
            50).style.set_precision(0).background_gradient(
            axis=0, gmap=pivot_past_30_days_orders['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Заказы за последние 30 дней, общая сумма -"
                                                                 f" {int(round(sum(pivot_past_30_days_orders['PriceWithDiscount']), 0))} (с учётом СПП),"
                                                                 f" общее количество - {sum(pivot_past_30_days_orders['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме заказов.")
    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    ##########   П   Р   О   Д   А   Ж   И      З   А   #########################################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


##########   П   Р   О   Д   А   Ж   И      З   А   #########################################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
##########   П   Р   О   Д   А   Ж   И      З   А   #########################################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

@dp.message_handler(commands="Продажи_по_товарам")
async def InlKB(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Продажи за сегодня", callback_data="Продажи_за_сегодня"))
    keyboard.add(types.InlineKeyboardButton(text="Продажи за вчера", callback_data="Продажи_за_вчера"))
    keyboard.add(types.InlineKeyboardButton(text="Продажи за эту неделю", callback_data="Продажи_за_эту_неделю"))
    keyboard.add(
        types.InlineKeyboardButton(text="Продажи за прошлую неделю", callback_data="Продажи_за_прошлую_неделю"))
    keyboard.add(types.InlineKeyboardButton(text="Продажи за этот месяц", callback_data="Продажи_за_этот_месяц"))
    keyboard.add(types.InlineKeyboardButton(text="Продажи за прошлый месяц", callback_data="Продажи_за_прошлый_месяц"))
    keyboard.add(
        types.InlineKeyboardButton(text="Продажи за последние 30 дней", callback_data="Продажи_за_последние_30_дней"))
    await message.answer("Выберите период, Продажи по которому вы хотите узнать", reply_markup=keyboard)


@dp.callback_query_handler(text="Продажи_за_сегодня")
async def sales(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        today_sales = sales[
            (sales['date'] >= str(current_date)) & (sales['IsStorno'] == 0) & (sales['PriceWithDiscount'] > 0)]
        pivot_today_sales = pd.merge(pd.pivot_table(today_sales, values='PriceWithDiscount', index=['supplierArticle'],
                                                    aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(today_sales,
                                                                  values='PriceWithDiscount', index=['supplierArticle'],
                                                                  aggfunc='sum', margins=False), how="left",
                                     left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(
            by=['PriceWithDiscount'],
            ascending=False, na_position='first').reset_index(drop=True)
        df_styled = pivot_today_sales[['supplierArticle', 'qty', 'PriceWithDiscount']].head(50).style.set_precision(
            0).background_gradient(
            axis=0, gmap=pivot_today_sales['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Продажи за сегодня, общая сумма -"
                                                                 f" {int(round(sum(pivot_today_sales['PriceWithDiscount']), 0))} (без учёта СПП),"
                                                                 f" общее количество - {sum(pivot_today_sales['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме продаж.")
    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(text="Продажи_за_вчера")
async def sales(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        yesterday_sales = sales[
            (sales['date'] < str(current_date)) & (sales['date'] >= str(current_date - timedelta(1)))
            & (sales['IsStorno'] == 0) & (sales['PriceWithDiscount'] > 0)]
        pivot_yesterday_sales = pd.merge(
            pd.pivot_table(yesterday_sales, values='PriceWithDiscount', index=['supplierArticle'],
                           aggfunc='count', margins=False).rename(columns={'PriceWithDiscount': 'qty'}),
            pd.pivot_table(yesterday_sales,
                           values='PriceWithDiscount', index=['supplierArticle'], aggfunc='sum', margins=False),
            how="left",
            left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(by=['PriceWithDiscount'],
                                                                                             ascending=False,
                                                                                             na_position='first').reset_index(
            drop=True)
        df_styled = pivot_yesterday_sales[['supplierArticle', 'qty', 'PriceWithDiscount']].head(50).style.set_precision(
            0).background_gradient(
            axis=0, gmap=pivot_yesterday_sales['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Продажи за вчера, общая сумма -"
                                                                 f" {int(round(sum(pivot_yesterday_sales['PriceWithDiscount']), 0))} (без учёта СПП),"
                                                                 f" общее количество - {sum(pivot_yesterday_sales['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме продаж.")
    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(text="Продажи_за_эту_неделю")
async def sales(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        sales['year_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.year
        week_sales = sales[
            (sales['week_num'] >= max(sales['week_num'])) & (sales['year_num'] >= max(sales['year_num'])) & (
                        sales['IsStorno'] == 0) & (sales['PriceWithDiscount'] > 0)]
        pivot_week_sales = pd.merge(pd.pivot_table(week_sales, values='PriceWithDiscount', index=['supplierArticle'],
                                                   aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(week_sales,
                                                                  values='PriceWithDiscount', index=['supplierArticle'],
                                                                  aggfunc='sum', margins=False), how="left",
                                    left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(
            by=['PriceWithDiscount'],
            ascending=False, na_position='first').reset_index(drop=True)
        df_styled = pivot_week_sales[['supplierArticle', 'qty', 'PriceWithDiscount']].head(50).style.set_precision(
            0).background_gradient(
            axis=0, gmap=pivot_week_sales['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Продажи за эту неделю, общая сумма -"
                                                                 f" {int(round(sum(pivot_week_sales['PriceWithDiscount']), 0))} (без учёта СПП),"
                                                                 f" общее количество - {sum(pivot_week_sales['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме продаж.")
    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(text="Продажи_за_прошлую_неделю")
async def sales(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        sales['year_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.year
        week_sales = sales[
            (sales['week_num'] == max(sales['week_num']) - 1) & (sales['year_num'] >= max(sales['year_num'])) & (
                        sales['IsStorno'] == 0) & (sales['PriceWithDiscount'] > 0)]
        pivot_week_sales = pd.merge(pd.pivot_table(week_sales, values='PriceWithDiscount', index=['supplierArticle'],
                                                   aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(week_sales,
                                                                  values='PriceWithDiscount', index=['supplierArticle'],
                                                                  aggfunc='sum', margins=False), how="left",
                                    left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(
            by=['PriceWithDiscount'],
            ascending=False, na_position='first').reset_index(drop=True)
        df_styled = pivot_week_sales[['supplierArticle', 'qty', 'PriceWithDiscount']].head(50).style.set_precision(
            0).background_gradient(
            axis=0, gmap=pivot_week_sales['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Продажи за прошлую неделю, общая сумма -"
                                                                 f" {int(round(sum(pivot_week_sales['PriceWithDiscount']), 0))} (без учёта СПП),"
                                                                 f" общее количество - {sum(pivot_week_sales['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме продаж.")
    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(text="Продажи_за_этот_месяц")
async def sales(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['month_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.month
        sales['year_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.year
        month_sales = sales[
            (sales['month_num'] == max(sales['month_num'])) & (sales['year_num'] >= max(sales['year_num'])) & (
                        sales['IsStorno'] == 0) & (sales['PriceWithDiscount'] > 0)]
        pivot_month_sales = pd.merge(pd.pivot_table(month_sales, values='PriceWithDiscount', index=['supplierArticle'],
                                                    aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(month_sales,
                                                                  values='PriceWithDiscount', index=['supplierArticle'],
                                                                  aggfunc='sum', margins=False), how="left",
                                     left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(
            by=['PriceWithDiscount'],
            ascending=False, na_position='first').reset_index(drop=True)
        df_styled = pivot_month_sales[['supplierArticle', 'qty', 'PriceWithDiscount']].head(50).style.set_precision(
            0).background_gradient(
            axis=0, gmap=pivot_month_sales['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Продажи за этот месяц, общая сумма -"
                                                                 f" {int(round(sum(pivot_month_sales['PriceWithDiscount']), 0))} (без учёта СПП),"
                                                                 f" общее количество - {sum(pivot_month_sales['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме продаж.")
    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(text="Продажи_за_прошлый_месяц")
async def sales(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['month_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.month
        sales['year_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.year
        month_sales = sales[
            (sales['month_num'] == max(sales['month_num']) - 1) & (sales['year_num'] >= max(sales['year_num'])) & (
                        sales['IsStorno'] == 0) & (sales['PriceWithDiscount'] > 0)]
        pivot_month_sales = pd.merge(pd.pivot_table(month_sales, values='PriceWithDiscount', index=['supplierArticle'],
                                                    aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(month_sales,
                                                                  values='PriceWithDiscount', index=['supplierArticle'],
                                                                  aggfunc='sum', margins=False), how="left",
                                     left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(
            by=['PriceWithDiscount'],
            ascending=False, na_position='first').reset_index(drop=True)
        df_styled = pivot_month_sales[['supplierArticle', 'qty', 'PriceWithDiscount']].head(50).style.set_precision(
            0).background_gradient(
            axis=0, gmap=pivot_month_sales['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Продажи за прошлый месяц, общая сумма -"
                                                                 f" {int(round(sum(pivot_month_sales['PriceWithDiscount']), 0))} (без учёта СПП),"
                                                                 f" общее количество - {sum(pivot_month_sales['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме продаж.")
    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(text="Продажи_за_последние_30_дней")
async def sales(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        past_30_days_sales = sales[(sales['date'] >= str(current_date - timedelta(30))) & (sales['IsStorno'] == 0) & (
                    sales['PriceWithDiscount'] > 0)]
        pivot_past_30_days_sales = pd.merge(
            pd.pivot_table(past_30_days_sales, values='PriceWithDiscount', index=['supplierArticle'],
                           aggfunc='count', margins=False).rename(columns={'PriceWithDiscount': 'qty'}),
            pd.pivot_table(past_30_days_sales,
                           values='PriceWithDiscount', index=['supplierArticle'], aggfunc='sum', margins=False),
            how="left",
            left_on='supplierArticle', right_on='supplierArticle').reset_index().sort_values(by=['PriceWithDiscount'],
                                                                                             ascending=False,
                                                                                             na_position='first').reset_index(
            drop=True)
        df_styled = pivot_past_30_days_sales[['supplierArticle', 'qty', 'PriceWithDiscount']].head(
            50).style.set_precision(0).background_gradient(
            axis=0, gmap=pivot_past_30_days_sales['PriceWithDiscount'], cmap='BuPu')
        dfi.export(df_styled, "D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png")
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mytable.png', 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=f"Продажи за последние 30 дней, общая сумма -"
                                                                 f" {int(round(sum(pivot_past_30_days_sales['PriceWithDiscount']), 0))} (без учёта СПП),"
                                                                 f" общее количество - {sum(pivot_past_30_days_sales['qty'])}.\nКартинкой выводится до топ 50 артикулов по сумме продаж.")
    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    ##########   ЗАКАЗЫ ПРОДАЖИ ГРАФИК   #########################################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


##########   ЗАКАЗЫ ПРОДАЖИ ГРАФИК   #########################################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
##########   ЗАКАЗЫ ПРОДАЖИ ГРАФИК   #########################################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

@dp.message_handler(commands="График_заказов_и_продаж")
async def InlKB(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="График за последние 7 дней", callback_data="За_последние_7_дней"))
    keyboard.add(types.InlineKeyboardButton(text="График за текущий месяц", callback_data="За_текущий_месяц"))
    keyboard.add(types.InlineKeyboardButton(text="График за последние 30 дней", callback_data="За_последние_30_дней"))
    keyboard.add(types.InlineKeyboardButton(text="График за 3 месяца", callback_data="За_3_месяца"))
    keyboard.add(types.InlineKeyboardButton(text="График за последние 90 дней", callback_data="За_последние_90_дней"))
    keyboard.add(types.InlineKeyboardButton(text="График за 6 месяцев", callback_data="За_6_месяцев"))
    keyboard.add(types.InlineKeyboardButton(text="График за последние 180 дней", callback_data="За_последние_180_дней"))
    keyboard.add(types.InlineKeyboardButton(text="График за текущий год", callback_data="За_текущий_год"))
    keyboard.add(types.InlineKeyboardButton(text="График за последние 365 дней", callback_data="За_последние_365_дней"))
    keyboard.add(types.InlineKeyboardButton(text="График за всё время", callback_data="За_всё_время"))
    await message.answer("Выберите период, заказы по которому вы хотите узнать", reply_markup=keyboard)


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(text="За_последние_7_дней")
async def graphics(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders = orders[(orders['date'] >= str(current_date - timedelta(6)))]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        orders['date'] = pd.to_datetime(orders['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        # orders['day_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.day
        # orders['week_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.isocalendar().week
        # orders['month_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.month
        # orders['year_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.year
        # orders['yearweek_num'] = (orders['year_num'].astype(str) + orders['week_num'].astype(str)).astype(int)
        pivot_orders = pd.merge(pd.pivot_table(orders, values='PriceWithDiscount', index=['date'],
                                               aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(orders,
                                                                  values='PriceWithDiscount', index=['date'],
                                                                  aggfunc='sum', margins=False), how="left",
                                left_on='date', right_on='date').reset_index().sort_values(by=['date'], ascending=True,
                                                                                           na_position='first').reset_index(
            drop=True)

        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales = sales[(sales['date'] >= str(current_date - timedelta(6)))]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['date'] = pd.to_datetime(sales['date']).dt.strftime('%Y-%m-%d')
        # sales['day_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.day
        # sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        # sales['month_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.month
        # sales['year_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.year
        # sales['yearweek_num'] = (sales['year_num'].astype(str) + sales['week_num'].astype(str)).astype(int)
        pivot_sales = pd.merge(pd.pivot_table(sales, values='PriceWithDiscount', index=['date'],
                                              aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(sales,
                                                                  values='PriceWithDiscount', index=['date'],
                                                                  aggfunc='sum', margins=False), how="left",
                               left_on='date', right_on='date').reset_index().sort_values(by=['date'], ascending=True,
                                                                                          na_position='first').reset_index(
            drop=True)

        plt.figure(figsize=(17, 9))
        plt.title('Статистика заказов (с СПП) и продаж (без СПП) по дням за последние 7 дней', fontsize=25)
        plt.ylabel('Рубли', fontsize=17)
        plt.xlabel('Дата', fontsize=17)
        plt.xticks(fontsize=15)
        plt.yticks(fontsize=15)
        plot(pivot_orders['date'], pivot_orders['PriceWithDiscount'], color='deeppink', marker='o', linestyle='dashed',
             linewidth=2, markersize=12, label='Заказы')
        plot(pivot_sales['date'], pivot_sales['PriceWithDiscount'], color='navy', marker='o', linestyle='dashed',
             linewidth=2, markersize=12, label='Продажи')
        plt.legend(loc="upper left", fontsize=15)
        plt.savefig('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', bbox_inches='tight')
        plt.close()
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', 'rb') as photo:
            await call.message.answer_photo(photo=photo,
                                            caption=f"Заказано за последние 7 дней {sum(pivot_orders['qty'])} шт на {int(round(sum(pivot_orders['PriceWithDiscount']), 0))} рублей.\n"
                                                    f"Продано за последние 7 дней {sum(pivot_sales['qty'])} шт на {int(round(sum(pivot_sales['PriceWithDiscount']), 0))} рублей.")


    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(text="За_текущий_месяц")
async def graphics(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        orders['date'] = pd.to_datetime(orders['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        # orders['day_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.day
        # orders['week_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.isocalendar().week
        orders['month_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.month
        orders['year_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.year
        # orders['yearweek_num'] = (orders['year_num'].astype(str) + orders['week_num'].astype(str)).astype(int)
        orders = orders[
            (orders['month_num'] >= max(orders['month_num'])) & (orders['year_num'] >= max(orders['year_num']))]
        pivot_orders = pd.merge(pd.pivot_table(orders, values='PriceWithDiscount', index=['date'],
                                               aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(orders,
                                                                  values='PriceWithDiscount', index=['date'],
                                                                  aggfunc='sum', margins=False), how="left",
                                left_on='date', right_on='date').reset_index().sort_values(by=['date'], ascending=True,
                                                                                           na_position='first').reset_index(
            drop=True)

        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['date'] = pd.to_datetime(sales['date']).dt.strftime('%Y-%m-%d')
        # sales['day_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.day
        # sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        sales['month_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.month
        sales['year_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.year
        # sales['yearweek_num'] = (sales['year_num'].astype(str) + sales['week_num'].astype(str)).astype(int)
        sales = sales[(sales['month_num'] >= max(sales['month_num'])) & (sales['year_num'] >= max(sales['year_num']))]
        pivot_sales = pd.merge(pd.pivot_table(sales, values='PriceWithDiscount', index=['date'],
                                              aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(sales,
                                                                  values='PriceWithDiscount', index=['date'],
                                                                  aggfunc='sum', margins=False), how="left",
                               left_on='date', right_on='date').reset_index().sort_values(by=['date'], ascending=True,
                                                                                          na_position='first').reset_index(
            drop=True)

        plt.figure(figsize=(17, 9))
        plt.title('Статистика заказов (с СПП) и продаж (без СПП) по дням за текущий месяц', fontsize=25)
        plt.ylabel('Рубли', fontsize=17)
        plt.xlabel('Дата', fontsize=17)
        plt.xticks(fontsize=15)
        plt.yticks(fontsize=15)
        plot(pd.to_datetime(pivot_orders['date'], errors='coerce').dt.day, pivot_orders['PriceWithDiscount'],
             color='deeppink', marker='o', linestyle='dashed',
             linewidth=2, markersize=12, label='Заказы')
        plot(pd.to_datetime(pivot_sales['date'], errors='coerce').dt.day, pivot_sales['PriceWithDiscount'],
             color='navy', marker='o', linestyle='dashed',
             linewidth=2, markersize=12, label='Продажи')
        plt.legend(loc="upper left", fontsize=15)
        plt.savefig('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', bbox_inches='tight')
        plt.close()
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', 'rb') as photo:
            await call.message.answer_photo(photo=photo,
                                            caption=f"Заказано за текущий месяц {sum(pivot_orders['qty'])} шт на {int(round(sum(pivot_orders['PriceWithDiscount']), 0))} рублей.\n"
                                                    f"Продано за текущий месяц {sum(pivot_sales['qty'])} шт на {int(round(sum(pivot_sales['PriceWithDiscount']), 0))} рублей.")


    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(text="За_последние_30_дней")
async def graphics(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders = orders[(orders['date'] >= str(current_date - timedelta(29)))]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        orders['date'] = pd.to_datetime(orders['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        # orders['day_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.day
        # orders['week_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.isocalendar().week
        # orders['month_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.month
        # orders['year_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.year
        # orders['yearweek_num'] = (orders['year_num'].astype(str) + orders['week_num'].astype(str)).astype(int)
        pivot_orders = pd.merge(pd.pivot_table(orders, values='PriceWithDiscount', index=['date'],
                                               aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(orders,
                                                                  values='PriceWithDiscount', index=['date'],
                                                                  aggfunc='sum', margins=False), how="left",
                                left_on='date', right_on='date').reset_index().sort_values(by=['date'], ascending=True,
                                                                                           na_position='first').reset_index(
            drop=True)

        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales = sales[(sales['date'] >= str(current_date - timedelta(29)))]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['date'] = pd.to_datetime(sales['date']).dt.strftime('%Y-%m-%d')
        # sales['day_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.day
        # sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        # sales['month_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.month
        # sales['year_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.year
        # sales['yearweek_num'] = (sales['year_num'].astype(str) + sales['week_num'].astype(str)).astype(int)
        pivot_sales = pd.merge(pd.pivot_table(sales, values='PriceWithDiscount', index=['date'],
                                              aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(sales,
                                                                  values='PriceWithDiscount', index=['date'],
                                                                  aggfunc='sum', margins=False), how="left",
                               left_on='date', right_on='date').reset_index().sort_values(by=['date'], ascending=True,
                                                                                          na_position='first').reset_index(
            drop=True)

        plt.figure(figsize=(17, 9))
        plt.title('Статистика заказов (с СПП) и продаж (без СПП) по дням за последние 30 дней', fontsize=25)
        plt.ylabel('Рубли', fontsize=17)
        plt.xlabel('Дата', fontsize=17)
        plt.xticks(fontsize=15)
        plt.yticks(fontsize=15)
        plot(pivot_orders['date'], pivot_orders['PriceWithDiscount'], color='deeppink', marker='o', linestyle='dashed',
             linewidth=2, markersize=12, label='Заказы')
        plot(pivot_sales['date'], pivot_sales['PriceWithDiscount'], color='navy', marker='o', linestyle='dashed',
             linewidth=2, markersize=12, label='Продажи')
        plt.legend(loc="upper left", fontsize=15)
        plt.savefig('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', bbox_inches='tight')
        plt.close()
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', 'rb') as photo:
            await call.message.answer_photo(photo=photo,
                                            caption=f"Заказано за последние 30 дней {sum(pivot_orders['qty'])} шт на {int(round(sum(pivot_orders['PriceWithDiscount']), 0))} рублей.\n"
                                                    f"Продано за последние 30 дней {sum(pivot_sales['qty'])} шт на {int(round(sum(pivot_sales['PriceWithDiscount']), 0))} рублей.")


    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(text="За_последние_90_дней")
async def graphics(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders = orders[(orders['date'] >= str(current_date - timedelta(89)))]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        orders['date'] = pd.to_datetime(orders['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        # orders['day_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.day
        orders['week_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.isocalendar().week
        # orders['month_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.month
        orders['year_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.year
        orders['yearweek_num'] = (orders['year_num'].astype(str) + orders['week_num'].astype(str)).astype(int)
        pivot_orders = pd.merge(pd.pivot_table(orders, values='PriceWithDiscount', index=['yearweek_num'],
                                               aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(orders,
                                                                  values='PriceWithDiscount', index=['yearweek_num'],
                                                                  aggfunc='sum', margins=False), how="left",
                                left_on='yearweek_num', right_on='yearweek_num').reset_index().sort_values(
            by=['yearweek_num'], ascending=True, na_position='first').reset_index(drop=True)

        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales = sales[(sales['date'] >= str(current_date - timedelta(89)))]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['date'] = pd.to_datetime(sales['date']).dt.strftime('%Y-%m-%d')
        # sales['day_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.day
        sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        # sales['month_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.month
        sales['year_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.year
        sales['yearweek_num'] = (sales['year_num'].astype(str) + sales['week_num'].astype(str)).astype(int)
        pivot_sales = pd.merge(pd.pivot_table(sales, values='PriceWithDiscount', index=['yearweek_num'],
                                              aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(sales,
                                                                  values='PriceWithDiscount', index=['yearweek_num'],
                                                                  aggfunc='sum', margins=False), how="left",
                               left_on='yearweek_num', right_on='yearweek_num').reset_index().sort_values(
            by=['yearweek_num'], ascending=True, na_position='first').reset_index(drop=True)

        plt.figure(figsize=(17, 9))
        plt.title('Статистика заказов (с СПП) и продаж (без СПП) по дням за последние 90 дней', fontsize=25)
        plt.ylabel('Рубли', fontsize=17)
        plt.xlabel('Номер недели в году в формате год_неделя', fontsize=17)
        plt.xticks(fontsize=15)
        plt.yticks(fontsize=15)
        plot(pivot_orders['yearweek_num'], pivot_orders['PriceWithDiscount'], color='deeppink', marker='o',
             linestyle='dashed',
             linewidth=2, markersize=12, label='Заказы')
        plot(pivot_sales['yearweek_num'], pivot_sales['PriceWithDiscount'], color='navy', marker='o',
             linestyle='dashed',
             linewidth=2, markersize=12, label='Продажи')
        plt.legend(loc="upper left", fontsize=15)
        plt.savefig('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', bbox_inches='tight')
        plt.close()
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', 'rb') as photo:
            await call.message.answer_photo(photo=photo,
                                            caption=f"Заказано за последние 90 дней {sum(pivot_orders['qty'])} шт на {int(round(sum(pivot_orders['PriceWithDiscount']), 0))} рублей.\n"
                                                    f"Продано за последние 90 дней {sum(pivot_sales['qty'])} шт на {int(round(sum(pivot_sales['PriceWithDiscount']), 0))} рублей.")


    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(text="За_последние_180_дней")
async def graphics(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders = orders[(orders['date'] >= str(current_date - timedelta(179)))]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        orders['date'] = pd.to_datetime(orders['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        # orders['day_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.day
        orders['week_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.isocalendar().week
        # orders['month_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.month
        orders['year_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.year
        orders['yearweek_num'] = (orders['year_num'].astype(str) + orders['week_num'].astype(str)).astype(int)
        pivot_orders = pd.merge(pd.pivot_table(orders, values='PriceWithDiscount', index=['yearweek_num'],
                                               aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(orders,
                                                                  values='PriceWithDiscount', index=['yearweek_num'],
                                                                  aggfunc='sum', margins=False), how="left",
                                left_on='yearweek_num', right_on='yearweek_num').reset_index().sort_values(
            by=['yearweek_num'], ascending=True, na_position='first').reset_index(drop=True)

        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales = sales[(sales['date'] >= str(current_date - timedelta(179)))]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['date'] = pd.to_datetime(sales['date']).dt.strftime('%Y-%m-%d')
        # sales['day_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.day
        sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        # sales['month_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.month
        sales['year_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.year
        sales['yearweek_num'] = (sales['year_num'].astype(str) + sales['week_num'].astype(str)).astype(int)
        pivot_sales = pd.merge(pd.pivot_table(sales, values='PriceWithDiscount', index=['yearweek_num'],
                                              aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(sales,
                                                                  values='PriceWithDiscount', index=['yearweek_num'],
                                                                  aggfunc='sum', margins=False), how="left",
                               left_on='yearweek_num', right_on='yearweek_num').reset_index().sort_values(
            by=['yearweek_num'], ascending=True, na_position='first').reset_index(drop=True)

        plt.figure(figsize=(17, 9))
        plt.title('Статистика заказов (с СПП) и продаж (без СПП) по дням за последние 180 дней', fontsize=25)
        plt.ylabel('Рубли', fontsize=17)
        plt.xlabel('Номер недели в году в формате год_неделя', fontsize=17)
        plt.xticks(fontsize=15)
        plt.yticks(fontsize=15)
        plot(pivot_orders['yearweek_num'], pivot_orders['PriceWithDiscount'], color='deeppink', marker='o',
             linestyle='dashed',
             linewidth=2, markersize=12, label='Заказы')
        plot(pivot_sales['yearweek_num'], pivot_sales['PriceWithDiscount'], color='navy', marker='o',
             linestyle='dashed',
             linewidth=2, markersize=12, label='Продажи')
        plt.legend(loc="upper left", fontsize=15)
        plt.savefig('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', bbox_inches='tight')
        plt.close()
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', 'rb') as photo:
            await call.message.answer_photo(photo=photo,
                                            caption=f"Заказано за последние 180 дней {sum(pivot_orders['qty'])} шт на {int(round(sum(pivot_orders['PriceWithDiscount']), 0))} рублей.\n"
                                                    f"Продано за последние 180 дней {sum(pivot_sales['qty'])} шт на {int(round(sum(pivot_sales['PriceWithDiscount']), 0))} рублей.")


    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(text="За_последние_365_дней")
async def graphics(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders = orders[(orders['date'] >= str(current_date - timedelta(364)))]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        orders['date'] = pd.to_datetime(orders['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        # orders['day_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.day
        orders['week_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.isocalendar().week
        # orders['month_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.month
        orders['year_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.year
        orders['yearweek_num'] = (orders['year_num'].astype(str) + orders['week_num'].astype(str)).astype(int)
        pivot_orders = pd.merge(pd.pivot_table(orders, values='PriceWithDiscount', index=['yearweek_num'],
                                               aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(orders,
                                                                  values='PriceWithDiscount', index=['yearweek_num'],
                                                                  aggfunc='sum', margins=False), how="left",
                                left_on='yearweek_num', right_on='yearweek_num').reset_index().sort_values(
            by=['yearweek_num'], ascending=True, na_position='first').reset_index(drop=True)

        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales = sales[(sales['date'] >= str(current_date - timedelta(364)))]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['date'] = pd.to_datetime(sales['date']).dt.strftime('%Y-%m-%d')
        # sales['day_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.day
        sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        # sales['month_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.month
        sales['year_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.year
        sales['yearweek_num'] = (sales['year_num'].astype(str) + sales['week_num'].astype(str)).astype(int)
        pivot_sales = pd.merge(pd.pivot_table(sales, values='PriceWithDiscount', index=['yearweek_num'],
                                              aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(sales,
                                                                  values='PriceWithDiscount', index=['yearweek_num'],
                                                                  aggfunc='sum', margins=False), how="left",
                               left_on='yearweek_num', right_on='yearweek_num').reset_index().sort_values(
            by=['yearweek_num'], ascending=True, na_position='first').reset_index(drop=True)

        plt.figure(figsize=(17, 9))
        plt.title('Статистика заказов (с СПП) и продаж (без СПП) по дням за последние 365 дней', fontsize=25)
        plt.ylabel('Рубли', fontsize=17)
        plt.xlabel('Номер недели в году в формате год_неделя', fontsize=17)
        plt.xticks(fontsize=15)
        plt.yticks(fontsize=15)
        plot(pivot_orders['yearweek_num'], pivot_orders['PriceWithDiscount'], color='deeppink', marker='o',
             linestyle='dashed',
             linewidth=2, markersize=12, label='Заказы')
        plot(pivot_sales['yearweek_num'], pivot_sales['PriceWithDiscount'], color='navy', marker='o',
             linestyle='dashed',
             linewidth=2, markersize=12, label='Продажи')
        plt.legend(loc="upper left", fontsize=15)
        plt.savefig('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', bbox_inches='tight')
        plt.close()
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', 'rb') as photo:
            await call.message.answer_photo(photo=photo,
                                            caption=f"Заказано за последние 365 дней {sum(pivot_orders['qty'])} шт на {int(round(sum(pivot_orders['PriceWithDiscount']), 0))} рублей.\n"
                                                    f"Продано за последние 365 дней {sum(pivot_sales['qty'])} шт на {int(round(sum(pivot_sales['PriceWithDiscount']), 0))} рублей.")


    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(text="За_всё_время")
async def graphics(call: types.CallbackQuery):
    try:
        current_date = date.today()
        response_orders = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'warehouseName', 'oblast', 'subject',
                'category', 'cancel_dt']
        orders = pd.DataFrame(json.loads(response_orders.content.decode('utf-8')))[cols]
        orders['PriceWithDiscount'] = orders['totalPrice'] * (1 - orders['discountPercent'] / 100)
        orders['date'] = pd.to_datetime(orders['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        # orders['day_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.day
        orders['week_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.isocalendar().week
        # orders['month_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.month
        orders['year_num'] = pd.to_datetime(orders['date'], errors='coerce').dt.year
        orders['yearweek_num'] = (orders['year_num'].astype(str) + orders['week_num'].astype(str)).astype(int)
        pivot_orders = pd.merge(pd.pivot_table(orders, values='PriceWithDiscount', index=['yearweek_num'],
                                               aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(orders,
                                                                  values='PriceWithDiscount', index=['yearweek_num'],
                                                                  aggfunc='sum', margins=False), how="left",
                                left_on='yearweek_num', right_on='yearweek_num').reset_index().sort_values(
            by=['yearweek_num'], ascending=True, na_position='first').reset_index(drop=True)

        response_sales = requests.get(
            'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom=2017-03-25T21%3A00%3A00.000Z&flag=0',
            headers={
                'Authorization': f'{df_user_api_excel[df_user_api_excel["user_id"] == str(call.from_user.id)]["user_api"][0]}'})
        cols = ['date', 'supplierArticle', 'totalPrice', 'discountPercent', 'promoCodeDiscount', 'warehouseName',
                'subject',
                'category', 'regionName', 'spp', 'forPay', 'finishedPrice', 'priceWithDisc', 'IsStorno']
        sales = pd.DataFrame(json.loads(response_sales.content.decode('utf-8')))[cols]
        sales['PriceWithDiscount'] = sales['totalPrice'] * ((100 - sales['discountPercent']) / 100) * (
                    (100 - sales['promoCodeDiscount']) / 100) * ((100 - sales['spp']) / 100)
        sales['date'] = pd.to_datetime(sales['date']).dt.strftime('%Y-%m-%d')
        # sales['day_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.day
        sales['week_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.isocalendar().week
        # sales['month_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.month
        sales['year_num'] = pd.to_datetime(sales['date'], errors='coerce').dt.year
        sales['yearweek_num'] = (sales['year_num'].astype(str) + sales['week_num'].astype(str)).astype(int)
        pivot_sales = pd.merge(pd.pivot_table(sales, values='PriceWithDiscount', index=['yearweek_num'],
                                              aggfunc='count', margins=False).rename(
            columns={'PriceWithDiscount': 'qty'}), pd.pivot_table(sales,
                                                                  values='PriceWithDiscount', index=['yearweek_num'],
                                                                  aggfunc='sum', margins=False), how="left",
                               left_on='yearweek_num', right_on='yearweek_num').reset_index().sort_values(
            by=['yearweek_num'], ascending=True, na_position='first').reset_index(drop=True)

        plt.figure(figsize=(17, 9))
        plt.title('Статистика заказов (с СПП) и продаж (без СПП) по неделям за всё время', fontsize=25)
        plt.ylabel('Рубли', fontsize=17)
        plt.xlabel('Номер недели в году в формате год_неделя', fontsize=17)
        plt.xticks(fontsize=15)
        plt.yticks(fontsize=15)
        plot(pivot_orders['yearweek_num'], pivot_orders['PriceWithDiscount'], color='deeppink', marker='o',
             linestyle='dashed',
             linewidth=2, markersize=12, label='Заказы')
        plot(pivot_sales['yearweek_num'], pivot_sales['PriceWithDiscount'], color='navy', marker='o',
             linestyle='dashed',
             linewidth=2, markersize=12, label='Продажи')
        plt.legend(loc="upper left", fontsize=15)
        plt.savefig('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', bbox_inches='tight')
        plt.close()
        with open('D:\грузи сюда\Всё по WB\ВСЁ НАШЕЕЕЕЕЕ\mygraph.jpg', 'rb') as photo:
            await call.message.answer_photo(photo=photo,
                                            caption=f"Заказано за всё время {sum(pivot_orders['qty'])} шт на {int(round(sum(pivot_orders['PriceWithDiscount']), 0))} рублей.\n"
                                                    f"Продано за всё время {sum(pivot_sales['qty'])} шт на {int(round(sum(pivot_sales['PriceWithDiscount']), 0))} рублей.")


    except:
        await call.message.answer('\U0001FAE0 Что-то пошло не так \U0001FAE0 \nНапиши создателю бота @dimi3_tru')

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
