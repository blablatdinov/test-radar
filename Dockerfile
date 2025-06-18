FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONNUMBUFFERED 1

WORKDIR /app

RUN apt update -y && pip install -U pip && pip install uv

COPY entrypoint.sh pyproject.toml uv.lock /app/
RUN uv pip install -r pyproject.toml --system
RUN chmod +x ./entrypoint.sh

COPY . /app
