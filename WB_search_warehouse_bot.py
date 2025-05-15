import requests
import pandas as pd
import time
import traceback
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile

import weasyprint as wsp
from PIL import Image, ImageChops
import pdf2image

import os
from dotenv import load_dotenv

load_dotenv()

SUPPLY_API_KEY = os.getenv('SUPPLY_API_KEY')
BOT_API_TOKEN = os.getenv('WB_Warehouse_Bot_DT')

# Инициализация бота
bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher()

# Параметры авторизации
headers = {
    "Authorization": SUPPLY_API_KEY,
    "Content-Type": "application/json",
}
url = 'https://supplies-api.wildberries.ru/api/v1/acceptance/coefficients'

needed_warehouse_ID = [
    507, # Коледино
    206348, # Тула
    117501, # Подольск
    120762, # Электросталь
    301760, # Рязань (Тюшевское)
    # 130744, # Краснодар (Тихорецкая)
    # 117986, # Казань
    # 208277, # Невинномысск
]
needed_boxTypeID = [2] # Короба
needed_coefficient = 20 # Максимальный коэффициент приёмки
TELEGRAM_USER_ID = '503499212'


def find_warehouse(headers, needed_warehouse_ID=None, 
                   needed_coefficient=1000, needed_boxTypeID=None):
    """
    Функция для поиска складов Wildberries, подходящих под заданные критерии.
    """
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    get_response_result = response.json()
    df_warehouse = pd.DataFrame(get_response_result)
    df_warehouse['date'] = pd.to_datetime(df_warehouse['date'].str.replace('Z', '', regex=False)).dt.strftime('%d-%m-%Y')

    if needed_warehouse_ID:
        df_warehouse = df_warehouse[df_warehouse['warehouseID'].isin(needed_warehouse_ID)]
    if needed_boxTypeID:
        df_warehouse = df_warehouse[df_warehouse['boxTypeID'].isin(needed_boxTypeID)]
    df_warehouse = df_warehouse[df_warehouse['coefficient'].between(0, needed_coefficient)]
    df_result = df_warehouse.drop(columns=['warehouseID', 'allowUnload', 'boxTypeName', 'boxTypeID', 'storageCoef', 
                                      'deliveryAdditionalLiter', 'storageBaseLiter', 'storageAdditionalLiter', 'isSortingCenter'])
    
    return df_result


async def send_telegram_message(chat_id: int, message: str):
    """
    Отправка сообщения пользователю в Telegram.
    """
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="MarkdownV2")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e} \n\n\nСообщение:\n{message}")

def df_to_pretty_text(df):
    if df.empty:
        return "Нет подходящих складов."
    lines = []
    header = (
        f"{'Дата':<10} | {'k':<1} | {'Склад':<15} | {'k дост':<6} | {'₽ дост':<6}"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for _, row in df.iterrows():
        lines.append(
            f"{row['date']:<10} | "
            f"{row['coefficient']:<1} | "
            f"{str(row['warehouseName'])[:15]:<15} | "
            f"{row['deliveryCoef']:<6} | "
            f"{row['deliveryBaseLiter']:<6}"
        )
    return "```\n" + "\n".join(lines) + "\n```"

# IMAGE

# def trim(source_filepath, target_filepath=None, background=None):
#     if not target_filepath:
#         target_filepath = source_filepath
#     img = Image.open(source_filepath)
#     if background is None:
#         background = img.getpixel((0, 0))
#     border = Image.new(img.mode, img.size, background)
#     diff = ImageChops.difference(img, border)
#     bbox = diff.getbbox()
#     img = img.crop(bbox) if bbox else img
#     img.save(target_filepath)

# def dataframe_to_image_file(df: pd.DataFrame, filename="table.png"):
#     # 1. Сгенерировать PDF
#     pdf_bytes = wsp.HTML(string=df.to_html(index=False)).write_pdf(stylesheets=[wsp.CSS(string='''
#         @page { size: auto; margin: 0; }
#         table, td, tr, th { border: 1px solid #444; border-collapse: collapse; }
#         td, th { padding: 6px 14px; font-size: 16px; }
#         th { background: #eaeaea; }
#     ''')])

#     # 2. PDF → PNG
#     # pdf2image конвертирует каждую страницу PDF в изображение
#     images = pdf2image.convert_from_bytes(pdf_bytes, dpi=200)
#     image = images[0]  # Только первая страница (если таблица большая и ушла на несколько страниц, можно склеить)
#     image.save(filename)
#     trim(filename)
#     return filename

# async def send_dataframe_as_image(chat_id: int, df: pd.DataFrame):
#     filename = "table1.png"
#     dataframe_to_image_file(df, filename)
#     with open(filename, "rb") as f:
#         photo = BufferedInputFile(f.read(), filename=filename)
#         await bot.send_photo(chat_id=chat_id, photo=photo)
#     os.remove(filename)



async def main():
    """
    Основной цикл с поиском складов и отправкой уведомлений.
    """
    request_count = 0

    while True:
        try:
            df_warehouse = find_warehouse(headers=headers,
                                          needed_warehouse_ID=needed_warehouse_ID,
                                          needed_coefficient=needed_coefficient,
                                          needed_boxTypeID=needed_boxTypeID)
            if not df_warehouse.empty:
                message = "Найдены подходящие склады:\n" + df_to_pretty_text(df_warehouse)
                await send_telegram_message(chat_id=int(TELEGRAM_USER_ID), message=message)
            # if not df_warehouse.empty:
            #     await send_telegram_message(chat_id=int(TELEGRAM_USER_ID), message="Найдены подходящие склады:")
            #     await send_dataframe_as_image(chat_id=int(TELEGRAM_USER_ID), df=df_warehouse)
            # if not df_warehouse.empty:
            #     message = "Найдены подходящие склады:\n" + df_warehouse.to_string(index=False)
            #     await send_telegram_message(chat_id=int(TELEGRAM_USER_ID), message=message)

            # Логируем в консоль каждые 25 запросов
            if request_count % 25 == 0:
                print(f"Время: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
                print(f"Выполнено запросов: {request_count}")
            
            request_count += 1
            await asyncio.sleep(12)
        
        except Exception as e:
            error_message = f"Ошибка:\n{e}\n{traceback.format_exc()}"
            print(error_message)
            await send_telegram_message(chat_id=int(TELEGRAM_USER_ID), message=error_message)
            await asyncio.sleep(60)  # Ждем 1 минуту перед повтором


# Запуск асинхронного бота
if __name__ == "__main__":
    # TELEGRAM_USER_ID = input("Введите ваш Telegram User ID: ").strip()  # Введите ID вручную
    TELEGRAM_USER_ID = '503499212'
    asyncio.run(main())
