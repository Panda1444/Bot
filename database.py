import aiosqlite
import asyncio

DB_NAME = "shop.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price INTEGER,
                description TEXT,
                stock INTEGER,
                data TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                amount INTEGER,
                invoice_id TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        await db.commit()

async def add_product(name, price, description, stock, data):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO products (name, price, description, stock, data) VALUES (?, ?, ?, ?, ?)",
                        (name, price, description, stock, data))
        await db.commit()

# Остальные функции БД добавим по ходу, если надо