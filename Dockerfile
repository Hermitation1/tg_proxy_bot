FROM python:3.14.4-slim
LABEL authors="Hermit"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR tgbot

COPY ./pyproject.toml .
COPY ./uv.lock .

RUN uv sync

COPY . .

CMD ["uv", "run", "python", "bot.py"]