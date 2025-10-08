from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from database import Analytics
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# Пример портфолио
portfolio_items = [
    {
        "title": "Бот для уведомлений",
        "description": "Интеграция с API, цена от 2000 руб.",
        "link": "https://t.me/channel/123"
    },
    {
        "title": "Бот для опросов",
        "description": "Сбор статистики и аналитика, цена от 3000 руб.",
        "link": "https://github.com/username/bot-survey"
    },
    {
        "title": "Интернет-магазин в Telegram",
        "description": "Каталог товаров и оплата, цена от 5000 руб.",
        "link": "https://t.me/channel/456"
    },
    # Добавьте еще примеры по необходимости
]

@router.message(Command(commands=['portfolio']))
async def cmd_portfolio(message: Message, session: AsyncSession):
    user_id = message.from_user.id

    # Логируем событие
    async with session.begin():
        session.add(Analytics(user_id=user_id, event='portfolio_view'))

    kb = InlineKeyboardBuilder()
    for item in portfolio_items:
        kb.button(
            text=item['title'],
            callback_data=f"portfolio_detail:{item['title']}"
        )
    kb.adjust(1)

    await message.answer("Портфолио проектов:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith('portfolio_detail:'))
async def portfolio_detail(call, session: AsyncSession):
    title = call.data.split(':', 1)[1]
    item = next((x for x in portfolio_items if x['title'] == title), None)
    if not item:
        await call.answer("Проект не найден", show_alert=True)
        return

    text = f"*{item['title']}*\n{item['description']}\n[Ссылка]({item['link']})"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Заказать похожий", callback_data="order_start")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
