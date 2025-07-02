# Telegram GPT-бот на Python (OpenAI + Yandex.Cloud)

## Описание

Этот бот реализован на Python с использованием библиотеки `pyTelegramBotAPI` и развёрнут через **Yandex Cloud Functions**.  
Он подключается к OpenAI через `ProxyAPI`, хранит историю переписки пользователей в **Object Storage (S3)** Яндекс.Облака и поддерживает работу с несколькими стилями общения.

Проект включает кастомную логику системных промптов, поддержку команд `/start`, `/reset` и Easter Eggs.

## Возможности

- Интерактивный Telegram-бот с поддержкой нескольких ролей общения
- Обработка команд `/start`, `/reset`, `/help`
- Сохранение истории диалога на стороне S3
- Кастомные промпты в зависимости от выбранной роли
- Поддержка Markdown (включая экранирование под MarkdownV2)
- Деплой на Yandex.Cloud Functions

## Установка и запуск локально

1. Клонировать репозиторий:

    ```bash
    git clone https://github.com/your_username/telegram_bot_api_gpt.git
    cd telegram_bot_api_gpt
    ```

2. Создать виртуальное окружение:

    ```bash
    python -m venv venv
    source venv/bin/activate       # для Linux/macOS
    .\venv\Scripts\activate        # для Windows
    ```

3. Установить зависимости:

    ```bash
    pip install -r requirements.txt
    ```

4. Создать файл `.env` и указать переменные окружения:

    ```
    TG_BOT_TOKEN=your_token_here
    TG_BOT_CHATS=123456789
    PROXY_API_KEY=your_openai_key
    YANDEX_KEY_ID=your_key_id
    YANDEX_KEY_SECRET=your_secret_key
    YANDEX_BUCKET=your_bucket_name
    ```

## Деплой на Yandex Cloud Functions

1. Упаковать проект в архив:

    ```bash
    zip -r function.zip .
    ```

2. Создать функцию в Yandex Cloud:

    - Рантайм: Python 3.10
    - Точка входа: `main.handler`
    - Загрузить `function.zip`
    - Задать переменные окружения из `.env`

3. Установить Webhook в Telegram:

    ```bash
    curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://functions.yandexcloud.net/<FUNCTION_ID>
    ```

4. Проверить работу бота в Telegram

## Структура проекта

    telegram_bot_api_gpt/
    ├── main.py               # Основной скрипт Telegram-бота
    ├── requirements.txt      # Список зависимостей проекта
    ├── .env                  # Файл с переменными окружения (не коммитится в репозиторий)
    ├── README.md             # Описание проекта
    ├── function.zip          # Архив для деплоя (опционально, если вы готовите вручную)
    └── /venv/                # Виртуальное окружение Python (исключается из репозитория)

й.

## Автор

Антон Гурский —  начинающий аналитик данных, увлечённый автоматизацией, Python и облачными технологиями.
