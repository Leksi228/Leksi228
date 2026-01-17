# Escort + Support Telegram Bots

## Установка

```bash
python -m pip install -U python-telegram-bot python-dotenv
```

## Настройка

Создай файл `.env` рядом с `config.py`:

```env
ESCORT_BOT_TOKEN=...
SUPPORT_BOT_TOKEN=...
ESCORT_ADMIN_IDS=123456789,987654321
ESCORT_LOG_CHAT_ID=-100123...   # (необязательно) чат для логов /start
SUPPORT_LOG_CHAT_ID=-100123...  # чат поддержки (форум с топиками)
ESCORT_DATA_FILE=escort_data.json
SUPPORT_DATA_FILE=support_data.json
```

## Запуск

```bash
python escort_bot.py
python support_bot.py
```

## Что сделано

- Город пользователя сохраняется навсегда (не перезаписывается обычными сообщениями).
- Главное меню полностью на inline-кнопках.
- Модели показываются списком на inline-кнопках, фильтрация по городу.
- Админка на inline-кнопках: добавление/редактирование/удаление моделей.
- «Дизайн» через админку: тексты, ссылка/название, подписи кнопок, выбор разделов главного меню.

