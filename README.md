# Двухсервисная система LLM-консультаций

## Описание проекта

Проект представляет собой двухсервисную систему для LLM-консультаций с авторизацией по JWT.

Система состоит из двух независимых сервисов:

- `auth_service` — сервис авторизации на FastAPI
- `bot_service` — Telegram-бот на aiogram, который принимает JWT, проверяет его и отправляет LLM-запросы через Celery

Архитектура построена по принципу разделения ответственности. `auth_service` отвечает только за регистрацию пользователей, логин и выпуск JWT-токенов. `bot_service` не хранит пользователей, не создаёт токены и не обращается напрямую к базе данных Auth Service. Он доверяет только корректно подписанному и не истёкшему JWT.

Для фоновой обработки LLM-запросов используются RabbitMQ, Redis и Celery. Telegram-бот не вызывает LLM напрямую в обработчике сообщения, а отправляет задачу в очередь. Celery worker забирает задачу, обращается к OpenRouter и отправляет ответ пользователю в Telegram.

---

## Архитектура

Основной сценарий работы:

```text
Пользователь
→ Auth Service /auth/register, /auth/login
→ получает JWT
→ отправляет JWT в Telegram-бота командой /token <jwt>
→ Bot Service валидирует JWT
→ сохраняет JWT в Redis по Telegram user_id
→ пользователь отправляет вопрос
→ Bot Service публикует задачу в RabbitMQ
→ Celery worker вызывает OpenRouter
→ ответ LLM отправляется пользователю в Telegram
```

## Роли компонентов

```text
auth_service:
- регистрация пользователя
- логин пользователя
- хеширование пароля
- выпуск JWT
- endpoint /auth/me

bot_service:
- Telegram-бот
- проверка JWT
- хранение токена в Redis
- отправка LLM-задач в Celery

RabbitMQ:
- брокер задач Celery

Redis:
- хранение JWT по Telegram user_id
- backend результатов Celery

Celery worker:
- обработка LLM-запросов
- вызов OpenRouter
- отправка ответа пользователю
```

---

## Структура проекта

```text
llm-consultation-system/
├── README.md
├── docker-compose.yml
├── .gitignore
├── docs/
│   └── screenshots/
│       ├── 01.1_auth_register.png
│       ├── 01.2_auth_register.png
│       ├── 02_auth_login.png
│       ├── 03_auth_me.png
│       ├── 04_telegram_token.png
│       ├── 05_telegram_llm_answer.png
│       ├── 06_celery_worker.png
│       ├── 07_rabbitmq_overview.png
│       ├── 08_rabbitmq_queues.png
│       ├── 09_ruff_check.png
│       ├── 10_auth_tests.png
│       └── 11_bot_tests.png
│
├── auth_service/
│   ├── pyproject.toml
│   ├── pytest.ini
│   ├── .env.example
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── exceptions.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── models.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── user.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── users.py
│   │   ├── usecases/
│   │   │   ├── __init__.py
│   │   │   └── auth.py
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── deps.py
│   │       ├── router.py
│   │       └── routes_auth.py
│   └── tests/
│       ├── __init__.py
│       ├── test_auth_api.py
│       └── test_security.py
│
└── bot_service/
    ├── pyproject.toml
    ├── pytest.ini
    ├── .env.example
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── config.py
    │   │   └── jwt.py
    │   ├── infra/
    │   │   ├── __init__.py
    │   │   ├── redis.py
    │   │   └── celery_app.py
    │   ├── services/
    │   │   ├── __init__.py
    │   │   └── openrouter_client.py
    │   ├── tasks/
    │   │   ├── __init__.py
    │   │   └── llm_tasks.py
    │   └── bot/
    │       ├── __init__.py
    │       ├── dispatcher.py
    │       ├── handlers.py
    │       └── run_bot.py
    └── tests/
        ├── __init__.py
        ├── test_handlers.py
        ├── test_jwt.py
        └── test_openrouter_client.py
```

---

## Переменные окружения

### `auth_service/.env`

```env
APP_NAME=auth-service
ENV=local

JWT_SECRET=change_me_super_secret
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

SQLITE_PATH=./auth.db
```

### `bot_service/.env`

```env
APP_NAME=bot-service
ENV=local

TELEGRAM_BOT_TOKEN=

JWT_SECRET=change_me_super_secret
JWT_ALG=HS256

REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672//

OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openrouter/free
OPENROUTER_SITE_URL=https://example.com
OPENROUTER_APP_NAME=bot-service
```

В обоих сервисах должен использоваться одинаковый `JWT_SECRET`, потому что `auth_service` создаёт JWT, а `bot_service` проверяет его подпись.

Файлы `.env` не добавляются в GitHub. Для примера настроек используются `.env.example`.

---

## Примечание по OpenRouter

В задании была указана модель:

```env
OPENROUTER_MODEL=stepfun/step-3.5-flash:free
```

Однако на момент тестирования эта конкретная бесплатная модель OpenRouter не позволяла выполнить запрос бесплатно и возвращала ошибку доступности free-версии. Поэтому для демонстрации работающей интеграции с OpenRouter была использована альтернативная бесплатная маршрутизируемая модель:

```env
OPENROUTER_MODEL=openrouter/free
```

`openrouter/free` позволяет направить запрос на доступную бесплатную модель OpenRouter. Это не меняет архитектуру проекта, потому что модель задаётся через переменную окружения и может быть заменена без изменения кода.

Клиент OpenRouter реализован отдельно в файле:

```text
bot_service/app/services/openrouter_client.py
```

Поэтому при необходимости можно вернуть исходную модель из задания или указать любую другую доступную модель OpenRouter через `.env`.

---

## Установка зависимостей

В проекте используется `uv`.

### Auth Service

```bash
cd auth_service
uv venv
source .venv/bin/activate
uv pip install -r <(uv pip compile pyproject.toml)
```

### Bot Service

```bash
cd bot_service
uv venv
source .venv/bin/activate
uv pip install -r <(uv pip compile pyproject.toml)
```

---

## Запуск инфраструктуры

Redis и RabbitMQ запускаются через Docker Compose:

```bash
docker compose up -d
```

Проверить запущенные контейнеры:

```bash
docker ps
```

RabbitMQ Management UI доступен по адресу:

```text
http://localhost:15672
```

Логин и пароль:

```text
guest / guest
```

---

## Запуск Auth Service

```bash
cd auth_service
source .venv/bin/activate
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger доступен по адресу:

```text
http://localhost:8000/docs
```

Реализованные endpoints:

```text
GET /health
POST /auth/register
POST /auth/login
GET /auth/me
```

---

## Запуск Celery worker

```bash
cd bot_service
source .venv/bin/activate
uv run celery -A app.infra.celery_app.celery_app worker --loglevel=info
```

При корректном запуске Celery видит задачу:

```text
[tasks]
  . llm_request
```

---

## Запуск Telegram-бота

```bash
cd bot_service
source .venv/bin/activate
uv run python -m app.bot.run_bot
```

---

## Пользовательский сценарий

1. Пользователь регистрируется в Auth Service через Swagger
2. Пользователь выполняет логин и получает JWT
3. Пользователь отправляет JWT Telegram-боту командой:

```text
/token <jwt>
```

4. Бот проверяет JWT и сохраняет его в Redis
5. Пользователь отправляет обычное текстовое сообщение
6. Бот проверяет наличие и валидность JWT
7. Бот отправляет LLM-запрос в Celery через RabbitMQ
8. Celery worker вызывает OpenRouter
9. Ответ LLM возвращается пользователю в Telegram

---

## Демонстрация работы

### 1. Регистрация пользователя в Auth Service

Пользователь регистрируется через endpoint `POST /auth/register`.  
В ответе возвращается публичная информация о пользователе без пароля и без `password_hash`.

![Регистрация пользователя](docs/screenshots/01.1_auth_register.png)

Дополнительный скриншот регистрации:

![Регистрация пользователя 2](docs/screenshots/01.2_auth_register.png)

---

### 2. Логин и получение JWT

После регистрации пользователь выполняет вход через `POST /auth/login`.  
В ответе сервис возвращает `access_token` и `token_type`.

![Логин пользователя](docs/screenshots/02_auth_login.png)

---

### 3. Получение профиля по JWT

Endpoint `GET /auth/me` доступен только при наличии валидного JWT.  
Токен передаётся через Swagger Authorize как Bearer token.

![Профиль пользователя](docs/screenshots/03_auth_me.png)

---

### 4. Передача JWT в Telegram-бота

Пользователь отправляет JWT Telegram-боту командой `/token <jwt>`.  
Бот проверяет подпись и срок действия токена, после чего сохраняет его в Redis, привязывая к Telegram user_id.

![Передача JWT в Telegram](docs/screenshots/04_telegram_token.png)

---

### 5. LLM-запрос через Telegram-бота

После сохранения токена пользователь может отправлять обычные текстовые вопросы.  
Бот не обращается к LLM напрямую, а публикует задачу в Celery через RabbitMQ.  
После обработки задачи Celery worker отправляет ответ пользователю в Telegram.

![LLM-запрос через Telegram](docs/screenshots/05_telegram_llm_answer.png)

---

### 6. Работа Celery worker

На скриншоте видно, что Celery worker зарегистрировал задачу `llm_request`, получил задачу из очереди и выполнил HTTP-запрос к OpenRouter.

![Работа Celery worker](docs/screenshots/06_celery_worker.png)

---

### 7. Работа RabbitMQ

RabbitMQ используется как брокер задач Celery.  
На скриншоте видно, что RabbitMQ запущен и участвует в системе: есть активные подключения, каналы, очереди и consumers.

![RabbitMQ Overview](docs/screenshots/07_rabbitmq_overview.png)

---

### 8. Очереди RabbitMQ

На скриншоте показана очередь Celery в RabbitMQ. Это подтверждает, что LLM-запросы проходят через очередь, а не выполняются напрямую в Telegram-хэндлере.

![RabbitMQ Queues](docs/screenshots/08_rabbitmq_queues.png)

---

## Тестирование и проверка качества кода

### 1. Проверка кода через Ruff

Для обоих сервисов выполнена проверка качества кода через `ruff`.

Команды запуска:

```bash
cd auth_service
uv run ruff check

cd ../bot_service
uv run ruff check
```

Результат:

![Ruff check](docs/screenshots/09_ruff_check.png)

---

### 2. Тесты Auth Service

Для `auth_service` реализованы unit и integration tests.

Команда запуска:

```bash
cd auth_service
uv run pytest
```

Проверяются:

- хеширование и проверка пароля
- создание и декодирование JWT
- регистрация пользователя
- логин пользователя
- получение профиля через `/auth/me`
- повторная регистрация с тем же email
- отказ при неправильном пароле
- отказ при запросе `/auth/me` без токена

Результат:

![Auth Service tests](docs/screenshots/10_auth_tests.png)

---

### 3. Тесты Bot Service

Для `bot_service` реализованы unit tests и mock tests.

Команда запуска:

```bash
cd bot_service
uv run pytest
```

Проверяются:

- декодирование валидного JWT
- отказ при невалидном JWT
- сохранение JWT через команду `/token`
- отказ при сообщении без токена
- отправка Celery-задачи при валидном токене
- клиент OpenRouter через мок `respx`

Результат:

![Bot Service tests](docs/screenshots/11_bot_tests.png)

---

## Что реализовано

В проекте реализованы:

- два независимых сервиса
- регистрация, логин и выпуск JWT в Auth Service
- хеширование паролей через bcrypt
- endpoint `/auth/me`, защищённый JWT
- проверка JWT в Bot Service без обращения к базе Auth Service
- команда `/token <jwt>` в Telegram-боте
- хранение токена Telegram-пользователя в Redis
- отправка LLM-запросов в Celery
- использование RabbitMQ как брокера задач
- использование Redis как хранилища токенов и backend Celery
- Celery worker для фоновой обработки LLM-запросов
- интеграция с OpenRouter
- обработка ошибок OpenRouter
- unit и integration tests
- проверка кода через Ruff
- демонстрационные скриншоты работы системы

---

## Итог

Проект демонстрирует работу распределённой двухсервисной системы, где Auth Service отвечает за пользователей и JWT, а Bot Service использует выданный токен для безопасного доступа к LLM-консультациям. Долгие LLM-запросы обрабатываются асинхронно через RabbitMQ и Celery, поэтому Telegram-бот остаётся отзывчивым и не блокируется во время ожидания ответа от модели.
