# TGProxyBot

Telegram-бот для сбора и проверки MTPROTO-прокси из публичных репозиториев.
Самовосстанавливается при потере связи с Telegram API через публичные SOCKS5/HTTP-прокси.

## Установка

### Локально

```bash
git clone <repo>
cd TGProxyBot
uv sync
cp .env.sample .env   # заполнить BOT_TOKEN
python bot.py
```

### Docker

```bash
docker build -t tgproxybot .
docker run -d --env-file .env tgproxybot
```

## Конфигурация

Все переменные окружения — в `.env`. Пример:

```env
BOT_TOKEN=123456:ABCdef
MTPROXY_SOURCES=["url1","url2"]
PROXIES_SOURCES=["url1","url2"]
CHECK_TIMEOUT=5
HEALTH_CHECK_INTERVAL=30
```

## Команды

| Команда | Описание |
|---|---|
| `/start` | Приветствие |
| `/check` | Скачать списки MTPROTO-прокси из GitHub, асинхронно проверить, выдать кнопками |

## Как это работает

1. **`/check`** → `fetch_proxy_sources()` качает raw-файлы с GitHub (без прокси, напрямую)
2. `check_mtproxies()` параллельно проверяет TCP-доступность каждого через `asyncio.gather()`
3. Результат возвращается inline-кнопками (ссылки `tg://proxy?...`)

4. **Health monitor** → фоновая задача раз в 30 сек пингует `api.telegram.org` через `bot.get_me()`
5. При обрыве → `check_proxies()` ищет первый рабочий SOCKS5/HTTP из публичных списков
6. Нашёлся → `core.bot.session` заменяется на новую `AiohttpSession(proxy=...)`
7. Параллельно `fill_proxies_pool()` пополняет пул из 5 прокси на будущее

## Структура

```
TGProxyBot/
├── bot.py              # Хендлеры, health_monitor, main()
├── core.py             # Bot, Dispatcher, proxy_pool
├── config.py           # Pydantic-settings
├── proxy_fetcher.py    # Загрузка списков из GitHub
├── proxy_checker.py    # Проверка MTPROTO и SOCKS5/HTTP
├── Dockerfile          # Docker-образ
├── .dockerignore
├── pyproject.toml      # Зависимости
└── .github/workflows/ci.yml
```