# KVINT: сервис результатов звонков

FastAPI-приложение с MongoDB и RabbitMQ.

## Запуск

Нужен Docker с Compose. Из корня проекта:

```bash
docker compose up --build
```

`.env` не обязателен. Для изменения настроек скопировать `.env.example` в `.env`.

| Сервис | Адрес |
| --- | --- |
| Swagger | http://localhost:8000/docs |
| Healthcheck | http://localhost:8000/health |
| RabbitMQ UI | http://localhost:15672 |
| RabbitMQ AMQP | localhost:5672 |
| MongoDB | localhost:27017 |

Учётные данные MongoDB и RabbitMQ: `app` / `app`.
База MongoDB: `kvint`, auth source: `admin`. RabbitMQ vhost: `/`.

## Проверка

```bash
curl http://localhost:8000/health
```

Ответ: `{"status":"ok"}`. Эндпоинт проверяет работу HTTP-приложения.

## Настройки

Все параметры перечислены в `.env.example`.
`MONGO_PORT` и `RABBITMQ_PORT` задают порты на хосте;
внутри Docker используются имена `mongo`, `rabbitmq` и стандартные порты.
`HEALTHCHECK_URL` — внутренний адрес проверки приложения, по умолчанию
`http://127.0.0.1:8000/health`.

Изменение учётных данных в `.env` не обновляет пользователей в существующих volumes.

## Логи и остановка

```bash
docker compose logs -f app
docker compose down
```

Данные сохраняются между запусками. Остановка с удалением всех данных:

```bash
docker compose down -v
```
