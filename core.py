from aiogram import Bot, Router, Dispatcher

from config import settings
from aiogram.client.session.aiohttp import AiohttpSession

session = AiohttpSession()

bot = Bot(token=settings.bot_token, session=session)
router = Router()
dp = Dispatcher()
dp.include_router(router)
proxy_pool: list[str] = []
