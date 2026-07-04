import asyncio
import logging

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import ClientError

import core
from config import settings
from core import dp, router
from proxy_checker import check_mtproxies, check_proxies, fill_proxies_pool
from proxy_fetcher import fetch_proxy_sources


logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def greetings(message: Message):
    await message.answer("Добро пожаловать в свободный интернет!")


@router.message(Command("check"))
async def check(message: Message):
    msg = await message.answer("Ищу...")
    proxies = await fetch_proxy_sources(sources=settings.mtproxy_sources)
    available_proxies = await check_mtproxies(proxies=proxies)

    if not available_proxies:
        await core.bot.send_message(message.chat.id, "Доступных прокси нет")
    else:
        await msg.edit_text("Нашел!")
        # lst = []
        # cnt = 0
        # for line in available_proxies:
        #     cnt += 1
        #     lst.append(f"{cnt}. {line}")
        #     if len(lst)%30 == 0:
        #         await core.bot.send_message(message.chat.id, "\n".join(lst))
        #         lst = []
        #
        # if lst:
        #     await core.bot.send_message(message.chat.id, "\n".join(lst))
        keyboard_rows = []
        for i, url in enumerate(available_proxies, 1):
            btn = InlineKeyboardButton(text=f"{i}. Подключить ✅", url=url)
            keyboard_rows.append([btn])

            if len(keyboard_rows) == 30 or i == len(available_proxies):
                markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
                await core.bot.send_message(message.chat.id, text=f"Лист прокси №{i // 30}", reply_markup=markup)
                keyboard_rows = []





async def health_monitor():
    while True:
        await asyncio.sleep(settings.health_check_interval)
        try:
            await core.bot.get_me()
        except Exception as e:
            logger.warning(f"Keepalive ping failed: {e}")

            if not core.proxy_pool:
                sources = await fetch_proxy_sources(
                    sources=settings.proxies_sources, proxy_type="socks"
                )
                new_proxy = await check_proxies(sources)
            else:
                sources = set(core.proxy_pool)
                new_proxy = await check_proxies(sources)

            if new_proxy:
                await core.bot.session.close()
                core.bot.session = AiohttpSession(proxy=new_proxy)
                logger.warning(f"New proxy is: {new_proxy}")
                if not core.proxy_pool:
                    _ = asyncio.create_task(
                        fill_proxies_pool(sources)
                    )  # asyncio: «Important: Save a reference to the result of this function, to avoid a task disappearing mid-execution.»
            else:
                if core.proxy_pool:
                    core.proxy_pool.clear()


async def main():
    try:
        asyncio.create_task(health_monitor())
        while True:
            try:
                await dp.start_polling(core.bot)
            except (
                TelegramNetworkError,
                ClientError,
            ):
                logger.warning("Polling failed, retrying in 5s...")
                await asyncio.sleep(5)
    finally:
        await core.bot.session.close()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
