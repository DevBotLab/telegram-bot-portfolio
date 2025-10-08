from aiogram import Router, F
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, PhotoSize
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import Order, Analytics, PromoCode
from config import ADMIN_ID, PAYMENT_CARDS
import logging

router = Router()

class OrderForm(StatesGroup):
    name = State()
    budget = State()
    description = State()
    promo_code = State()

@router.message(Command(commands=['order']))
async def cmd_order_start(message: Message, state: FSMContext):
    await message.answer("Введите ваше имя:")
    await state.set_state(OrderForm.name)

@router.message(OrderForm.name)
async def order_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш бюджет (от 2000 руб.):")
    await state.set_state(OrderForm.budget)

@router.message(OrderForm.budget)
async def order_budget(message: Message, state: FSMContext):
    try:
        budget = int(message.text)
        if budget < 2000:
            await message.answer("Бюджет должен быть не менее 2000 руб. Попробуйте еще раз.")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите число.")
        return
    await state.update_data(budget=budget)
    await message.answer("Опишите ваш проект:")
    await state.set_state(OrderForm.description)

@router.message(OrderForm.description)
async def order_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите промокод (если есть, иначе 'нет'):")
    await state.set_state(OrderForm.promo_code)

@router.message(OrderForm.promo_code)
async def order_promo(message: Message, state: FSMContext, session: AsyncSession):
    promo_input = message.text.strip().lower()
    discount = 0
    promo_id = None

    if promo_input != 'нет':
        async with session.begin():
            result = await session.execute(
                select(PromoCode).where(PromoCode.code == promo_input, PromoCode.used == False)
            )
            promo = result.scalars().first()
            if promo:
                discount = promo.discount if promo.discount_type == 'fixed' else (promo.discount / 100)
                promo_id = promo.id
            else:
                await message.answer("Промокод недействителен. Продолжаем без скидки.")
    
    data = await state.get_data()
    final_budget = data['budget'] - discount if promo_id else data['budget']

    # Сохраняем заказ в БД
    try:
        order = Order(
            user_id=message.from_user.id,
            name=data['name'],
            budget=final_budget,
            description=data['description'],
            status='new'
        )
        async with session.begin():
            session.add(order)
            session.add(Analytics(user_id=message.from_user.id, event='order_submit'))
            if promo_id:
                promo.used = True
                promo.used_by = message.from_user.id
    except Exception as e:
        logging.error(f"Ошибка сохранения заказа: {e}")
        await message.answer("Произошла ошибка при сохранении заказа. Попробуйте позже.")
        await state.clear()
        return

    # Отправляем админу заявку
    admin_text = (
        f"Новая заявка от @{message.from_user.username or 'пользователь'} (ID: {message.from_user.id}):\n"
        f"Имя: {data['name']}\n"
        f"Бюджет: {final_budget} руб.\n"
        f"Описание: {data['description']}\n"
        f"Промокод: {promo_input if promo_id else 'нет'}"
    )
    await message.bot.send_message(chat_id=ADMIN_ID, text=admin_text)

    # Инструкции по оплате
    payment_text = (
        f"Заявка принята! Итоговая сумма: {final_budget} руб.\n"
        f"Оплатите на карту:\n"
        f"Сбер: {PAYMENT_CARDS['sber']}\n"
        f"Тинькофф: {PAYMENT_CARDS['tinkoff']}\n"
        f"После оплаты пришлите скриншот чека для проверки."
    )
    await message.answer(payment_text, reply_markup=ReplyKeyboardRemove())
    await state.clear()

# Обработка скриншота оплаты
@router.message(F.photo)
async def handle_payment_screenshot(message: Message, session: AsyncSession):
    # Предполагаем, что это скриншот для последнего заказа
    user_id = message.from_user.id
    async with session.begin():
        result = await session.execute(
            select(Order).where(Order.user_id == user_id).order_by(Order.id.desc())
        )
        order = result.scalars().first()
        if order and order.status == 'new':
            # Отправляем админу скриншот
            await message.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=message.photo[-1].file_id,
                caption=f"Скриншот оплаты от @{message.from_user.username} (ID: {user_id}) для заказа #{order.id}"
            )
            await message.answer("Скриншот отправлен на проверку. Ожидайте подтверждения.")
        else:
            await message.answer("Не найдено активного заказа для оплаты.")

# Админ команда для создания промокода
@router.message(Command(commands=['create_promo']))
async def cmd_create_promo(message: Message, session: AsyncSession):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещен.")
        return

    # Парсим аргументы: /create_promo CODE DISCOUNT TYPE (percent or fixed)
    args = message.text.split()
    if len(args) < 4:
        await message.answer("Использование: /create_promo <код> <скидка> <тип: percent или fixed>")
        return

    code = args[1].upper()
    try:
        discount = int(args[2])
    except ValueError:
        await message.answer("Скидка должна быть числом.")
        return

    discount_type = args[3].lower()
    if discount_type not in ['percent', 'fixed']:
        await message.answer("Тип скидки: percent или fixed.")
        return

    try:
        promo = PromoCode(code=code, discount=discount, discount_type=discount_type)
        async with session.begin():
            session.add(promo)
        await message.answer(f"Промокод {code} создан.")
    except Exception as e:
        await message.answer(f"Ошибка создания промокода: {e}")
