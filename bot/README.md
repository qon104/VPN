# VPN Telegram Bot (aiogram 3 + Stars)

Бот для продажи VPN-подписок с оплатой через **Telegram Stars**.

## Структура

```
bot/
├── .env.example
├── requirements.txt
├── main.py
├── loader.py
├── handlers/
│   ├── start.py
│   ├── buy.py
│   ├── my_subscription.py
│   ├── download.py
│   └── admin.py
├── keyboards/
│   ├── inline.py
│   └── reply.py
├── services/
│   ├── payment.py
│   ├── key.py
│   └── user.py
├── middlewares/
│   └── auth.py
└── states/
    └── payment.py
```

## Установка

```bash
cd bot
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Отредактируй .env
```

## Настройка `.env`

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен от @BotFather |
| `ADMIN_IDS` | ID админов через запятую |
| `BACKEND_URL` | URL твоего VPN-backend (Marzban / 3x-ui / свой) |
| `BACKEND_API_KEY` | API-ключ backend |
| `PRICE_*` | Цены тарифов в Stars |

## Запуск

```bash
cd bot
python main.py
```

## Важно

1. **Telegram Stars**  
   Оплата работает только если у бота включены платежи и Stars.  
   `provider_token` оставляем пустым, валюта `XTR`.

2. **Backend ключей** (`services/key.py`)  
   Сейчас есть рабочий fallback (заглушка).  
   Подставь свой endpoint под Marzban / 3x-ui / Remnawave и т.д.

3. **Админка**  
   Команда `/admin` доступна только ID из `ADMIN_IDS`.

## Тарифы (по умолчанию)

| Тариф | Дней | Stars |
|---|---|---|
| 1 месяц | 30 | 150 |
| 3 месяца | 90 | 400 |
| 6 месяцев | 180 | 700 |
| 12 месяцев | 365 | 1200 |

Меняй цены в `.env`.
