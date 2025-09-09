# Облачная инфраструктура

## Настройка окружения

С помощью [UV](https://docs.astral.sh/uv/)
```bash
uv sync
```

С помощью pip
```bash
pip install -r requirements.txt
```

Для работы скрипта необходимо создать `.env` файл и заполнить значения переменных окружений по аналогии с [.env.example](.env.example)
## Код-стайл

```bash
uv run ruff format .
uv run ruff check . --fix
```

## Запуск скрипта
### Пополнить баланс песочницы Т-Инвестиций

UV:
```bash
uv run main.py add-funds
```
Python:
```bash
python main.py add-funds
```
### Запустить скрипт торговли в песочнице Т-Инвестиций
UV:
```bash
uv run main.py start-trading
```
Python:
```bash
python main.py start-trading
```
### Удалить все брокерские счета в песочнице Т-Инвестиций
UV:
```bash
uv run main.py delete-accounts
```
Python:
```bash
python main.py delete-accounts
```