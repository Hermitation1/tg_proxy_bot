import asyncio
from asyncio import IncompleteReadError
from urllib.parse import urlparse, parse_qs
import logging

import aiohttp
from aiohttp import ClientError
from aiohttp_socks import ProxyConnector, ProxyConnectionError, ProxyError

import core
from config import settings


logger = logging.getLogger(__name__)
sem = asyncio.Semaphore(50)


# CHECKING MTPROTO PROXIES
async def check_mtproxies(proxies: set):
    tasks = [check_mtproxy(url) for url in proxies]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    available_proxies = list(filter(None, results))

    return available_proxies


async def check_mtproxy(url: str):
    async with sem:
        params = parse_qs(urlparse(url).query)
        server = params["server"][0]
        port = int(params["port"][0])
        try:
            await asyncio.wait_for(
                asyncio.open_connection(host=server, port=port),
                timeout=settings.check_timeout,
            )
            return url

        except (
            OSError,
            TimeoutError,
            ConnectionRefusedError,
            ProxyConnectionError,
            ProxyError,
        ):
            return None


# CHECKING SOCKS/HTTP/HTTPS PROXIES
async def check_proxies(proxies: set):
    tasks = [
        asyncio.create_task(check_proxy(url)) for url in proxies
    ]  # If do it without create_task - coroutines can't be canceled, but tasks could
    for coro in asyncio.as_completed(tasks):
        url = await coro
        if url is not None:
            for t in tasks:
                t.cancel()
            return url
    return None


async def check_proxy(url: str):
    async with sem:
        connector = ProxyConnector.from_url(url)
        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                resp = await asyncio.wait_for(
                    session.get("https://api.telegram.org"),
                    timeout=settings.check_timeout,
                )
                if resp.ok:
                    await resp.read()
                    return url

        except (
            OSError,
            TimeoutError,
            ConnectionRefusedError,
            ClientError,
            ProxyError,
            ProxyConnectionError,
            IncompleteReadError,
        ):
            return None


async def fill_proxies_pool(sources: set, count: int = 5):
    tasks = [check_proxy(url) for url in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    available_proxies = [
        r
        for r in results
        if isinstance(r, str) and r.startswith(("socks5://", "http://", "https://"))
    ]

    core.proxy_pool = available_proxies[:count]
    return len(core.proxy_pool)
