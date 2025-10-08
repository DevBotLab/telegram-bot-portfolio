from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import User, Analytics
from config import CHANNEL_ID, ADMIN_ID
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot
import logging

router = Router()

async def check_subscription(bot: Bot, user_id: int, session: AsyncSession) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        return False

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, session: AsyncSession):
    user_id = message.from_user.id
    username = message.from_user.username

    # Проверяем подписку
    subscribed = await check_subscription(bot, user_id, session)

    # Добавляем или обновляем пользователя в БД
    async with session.begin():
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            user = User(id=user_id, username=username, subscribed=subscribed)
            session.add(user)
        else:
            user.subscribed = subscribed
            user.username = username

    # Логируем событие
    async with session.begin():
        session.add(Analytics(user_id=user_id, event='start'))

    if not subscribed:
        # Определяем ссылку на канал
        if CHANNEL_ID.startswith('-100'):
            channel_link = f"https://t.me/c/{CHANNEL_ID[4:]}"
        else:
            channel_link = f"https://t.me/{CHANNEL_ID.lstrip('@')}"

        kb = InlineKeyboardBuilder()
        kb.button(text='Подписаться', url=channel_link)
        kb.button(text='Проверить подписку', callback_data='check_sub')
        kb.adjust(2)
        await message.answer(
            f"Для доступа подпишись на канал: {channel_link}",
            reply_markup=kb.as_markup()
        )
        return

    # Если подписан, показываем главное меню
    await message.answer("Добро пожаловать! Главное меню будет здесь после проверки подписки.")
    # TODO: Вызвать функцию показа главного меню

@router.callback_query(F.data == 'check_sub')
async def callback_check_sub(call: CallbackQuery, bot: Bot, session: AsyncSession):
    user_id = call.from_user.id
    subscribed = await check_subscription(bot, user_id, session)

    async with session.begin():
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.subscribed = subscribed

    if subscribed:
        await call.message.edit_text("Подписка подтверждена! Главное меню будет здесь.")
        # TODO: Вызвать функцию показа главного меню
    else:
        await call.answer("Вы все еще не подписаны на канал.", show_alert=True)
