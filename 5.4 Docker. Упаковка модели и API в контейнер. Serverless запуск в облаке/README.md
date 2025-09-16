# API для совершения сделок на основе сигналов

## Краткое описание:
API имеет 3 эндопинта:

- `/trading/add_funds` - добавляет средства на брокерский счёт песочницы Т-Инвестиций
- `/trading/execute_trade` - совершает сделку в песочнице Т-Инвестиций
- `/trading/delete_accounts` - удаляет все брокерские счета из песочницы Т-Инвестиций


В `/trading/add_funds` добавлена самая простая реализация [ключа идемпотентности](https://habr.com/ru/companies/domclick/articles/779872/?ysclid=mfh3mshtmu911847986) - считываем ключ из хедеров запроса и храним в памяти запущенного сервиса 

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

## Запуск докер контейнера
Сборка образа
```bash
docker build -t <имя образа> .
```

Запуск контейнера из образа с монтированием внешнего хранилища для логов
```bash
docker run -v <путь к локальной папке с логами>/logs:/home/python/app/logs -p <PORT>:<PORT> --env-file <путь к .env файлу> <имя образа>
```
Запуск контейнера из образа без сохранения логов в файл
```bash
docker run -p <PORT>:<PORT> --env-file <путь к .env файлу> <имя образа>
```

