import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, func

Base = declarative_base()

# Создаем асинхронный движок и сессию
engine = create_async_engine(
    "sqlite+aiosqlite:///db.sqlite",
    echo=False,
    future=True,
)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Модели базы данных

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)  # user_id Telegram
    username = Column(String, nullable=True)
    is_blocked = Column(Boolean, default=False)
    subscribed = Column(Boolean, default=False)
    opt_in = Column(Boolean, default=True)  # для рассылок
    referral_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    referral_points = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    referrals = relationship("User", remote_side=[id])

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    budget = Column(Integer)
    description = Column(Text)
    status = Column(String, default='new')  # new, processed, paid
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Analytics(Base):
    __tablename__ = 'analytics'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    event = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    user_name = Column(String)
    text = Column(Text)
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LessonProgress(Base):
    __tablename__ = 'lesson_progress'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    lesson_index = Column(Integer, default=0)
    completed = Column(Boolean, default=False)

class Referral(Base):
    __tablename__ = 'referrals'
    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey('users.id'))
    referred_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CalendarEvent(Base):
    __tablename__ = 'calendar_events'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    text = Column(String)
    event_time = Column(DateTime)

class ForumPost(Base):
    __tablename__ = 'forum_posts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    topic = Column(String)
    text = Column(Text)
    pinned = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PromoCode(Base):
    __tablename__ = 'promo_codes'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    discount = Column(Integer)  # процент скидки или сумма
    discount_type = Column(String, default='percent')  # percent or fixed
    used = Column(Boolean, default=False)
    used_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Функция для создания таблиц
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
