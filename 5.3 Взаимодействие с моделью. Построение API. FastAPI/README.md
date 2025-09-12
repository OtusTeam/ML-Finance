# API для ML модели

## Краткое описание:
API имеет 4 эндопинта:

- `/add_funds` - добавляет средства на брокерский счёт песочницы Т-Инвестиций
- `/start_trading` - запускает торговую стратегию в песочнице Т-Инвестиций в отдельном треде
- `/stop_trading` - останавливает запущенную торговую стратегию в песочнице Т-Инвестиций
- `/delete_accounts` - удаляет все брокерские счета из песочницы Т-Инвестиций


В `/add_funds` добавлена самая простая реализация [ключа идемпотентности](https://habr.com/ru/companies/domclick/articles/779872/?ysclid=mfh3mshtmu911847986) - считываем ключ из хедеров запроса и храним в памяти запущенного сервиса 

## Основные модули:

- [Модуль с реализацией эндпоинтов](app/routes/trading_routes.py)
- [Модуль с торговой стратегией](app/trading_strategy.py)
- [Модуль с FastAPI приложением](app/fastapi.py)
- [Модуль с настройками приложения](app/settings.py)
- [Точка входа для запуска API](main.py) 

## Настройка окружения

С помощью [UV](https://docs.astral.sh/uv/)
```bash
uv sync
```

С помощью pip
```bash
pip install -r requirements.txt
```

Для работы API необходимо создать `.env` файл и заполнить значения переменных окружения по аналогии с [.env.example](.env.example)
## Код-стайл

```bash
uv run ruff format .
uv run ruff check . --fix
```

## Запуск API
UV:
```bash
uv run main.py
```
Python:
```bash
python main.py
```