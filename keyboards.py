from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Каталог"))
    kb.add(KeyboardButton("Мои заказы"), KeyboardButton("Поддержка"))
    return kb

def get_admin_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Добавить товар"), KeyboardButton("Заказы"))
    kb.add(KeyboardButton("Статистика"), KeyboardButton("Рассылка"))
    kb.add(KeyboardButton("Назад в магазин"))
    return kb

def product_inline(product_id, name, price):
    ikb = InlineKeyboardMarkup()
    ikb.add(InlineKeyboardButton(f"Купить {name} — {price}₽", callback_data=f"buy_{product_id}"))
    return ikb