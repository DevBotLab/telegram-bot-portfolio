from .start import router as start_router
from .portfolio import router as portfolio_router
from .order import router as order_router

# Импортируйте другие роутеры здесь
# from .broadcast import router as broadcast_router
# etc.

__all__ = ['start_router', 'portfolio_router', 'order_router']
