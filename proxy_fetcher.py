import asyncio
import aiohttp
import logging


logger = logging.getLogger(__name__)


async def fetch_proxy_sources(sources: list[str], proxy_type: str = "mtproto") -> set:
    proxy_list = []
    async with aiohttp.ClientSession() as session:
        for ln in sources:
            try:
                async with session.get(ln, timeout=15) as response:
                    response.raise_for_status()
                    html = await response.text()
            except (
                aiohttp.ClientError,
                OSError,
                asyncio.TimeoutError,
            ) as e:
                logger.warning(f"Failed to fetch {ln}: {e}")
                continue

            for line in html.split("\n"):
                # CHECKING MTPROTO PROXIES
                if proxy_type == "mtproto" and line.startswith(
                    "https://t.me/proxy?server="
                ):
                    proxy_list.append(line)

                # CHECKING SOCKS/HTTP/HTTPS PROXIES
                elif proxy_type == "socks" and line.startswith(
                    ("socks5://", "http://", "https://")
                ):
                    proxy_list.append(line)

    return set(proxy_list)
