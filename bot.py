import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

import requests
import json

from config import BOT_TOKEN, APIROLE_TOKEN, APIROLE_SHOP_ID, ADMIN_ID
from database import init_db
from keyboards import get_main_menu, get_admin_menu, product_inline

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class OrderStates(StatesGroup):
    waiting_quantity = State()

# === Команды ===
@dp.message(Command("start"))
async def start(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Привет, хозяин!", reply_markup=get_admin_menu())
    else:
        await message.answer("Добро пожаловать в магазин!", reply_markup=get_main_menu())
    
    # Покажем один товар для примера (можно добавить в БД)
    await show_catalog(message)

async def show_catalog(message: Message):
    # Пример товара (в реальности берём из БД)
    await message.answer_photo(
        photo="https://i.imgur.com/example.jpg",
        caption="<b>VPN Premium</b>\nЦена: 299₽\nСрок: 30 дней",
        reply_markup=product_inline(1, "VPN Premium", 299)
    )

# === Покупка ===
@dp.callback_query(F.data.startswith("buy_"))
async def buy_product(call: CallbackQuery, state: FSMContext):
    product_id = int(call.data.split("_")[1])
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(f"Введите количество (1–100):")
    await state.update_data(product_id=product_id, price=299)  # потом из БД
    await state.set_state(OrderStates.waiting_quantity)

@dp.message(OrderStates.waiting_quantity)
async def process_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 100):
        await message.answer("Введите число от 1 до 100")
        return
    
    qty = int(message.text)
    data = await state.get_data()
    total = data["price"] * qty
    
    # Создаём счёт через APIrole
    url = "https://api.apirole.com/v1/invoices/create"
    payload = {
        "shop_id": APIROLE_SHOP_ID,
        "amount": total,
        "currency": "RUB",
        "description": f"Покупка товара #{data['product_id']} ×{qty}",
        "success_url": "https://t.me/yourshopbot",  # можно оставить так
        "custom": str(message.from_user.id)
    }
    headers = {"Authorization": f"Bearer {APIROLE_TOKEN}"}
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        await message.answer("Ошибка создания счёта, попробуйте позже")
        return
    
    result = response.json()
    invoice_id = result["id"]
    pay_url = result["pay_url"]
    
    # Сохраняем заказ (пока просто в памяти)
    await state.update_data(invoice_id=invoice_id)
    
    await message.answer(
        f"Счёт на {total}₽ создан!\n"
        f"Оплатите в течение 15 минут:\n{pay_url}",
        disable_web_page_preview=True
    )
    
    # Автопроверка оплаты каждые 5 сек
    asyncio.create_task(check_payment(invoice_id, message.from_user.id, data["product_id"], qty))

async def check_payment(invoice_id: str, user_id: int, product_id: int, qty: int):
    url = f"https://api.apirole.com/v1/invoices/{invoice_id}"
    headers = {"Authorization": f"Bearer {APIROLE_TOKEN}"}
    
    for _ in range(180):  # 15 минут
        await asyncio.sleep(5)
        r = requests.get(url, headers=headers)
        if r.status_code == 200 and r.json().get("status") == "paid":
            # ВЫДАЧА ТОВАРА
            await bot.send_message(user_id, 
                f"Оплата прошла!\n\n"
                f"Ваш товар:\n"
                f"https://example-vpn-config.com/user123.ovpn\n"
                f"Логин: user123\nПароль: pass123"
            )
            return
    await bot.send_message(user_id, "Время оплаты истекло")

# === Админка ===
@dp.message(F.text == "Добавить товар")
async def add_product_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Функция в разработке — скоро будет добавление через /add name|price|desc|stock|data")

# Запуск
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())