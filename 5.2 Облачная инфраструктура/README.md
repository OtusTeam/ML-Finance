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
## Код-стайл

```bash
uv run ruff format .
uv run ruff check . --fix
```

## Запуск скрипта
### Пополнить баланс песочницы Т-Инвестций

UV:
```bash
uv run main.py add-funds
```
Python:
```bash
python main.py add-funds
```
### Запустить скрипт торговли в песочнице Т-Инвестций
UV:
```bash
uv run main.py start-trading
```
Python:
```bash
python main.py start-trading
```
### Удалить все брокерские счета в песочнице Т-Инвестций
UV:
```bash
uv run main.py delete-accounts
```
Python:
```bash
python main.py delete-accounts
```