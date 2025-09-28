# Docker compose. Разворачивание микросервисной архитектуры

## Краткое описание

Запускается 6 сервисов
- `ML Signals` - рассчитывает сигналы на основе рыночных данных с помощью ML модели
- `API Trader` - взаимодействует с песочницей Т-Инвестиций
- `Prometheus` - собирает метрики из сервисов
- `Grafana` - дашборды для мониторинга
- `Alertmanager` - отправка алертов в различные каналы
- `Nginx` - реверс-прокси и единая точка доступа (опционально - балансировка)

####  Запуск всех сервисов

1. Запуск всех сервисов из `docker-compose.yml` в единственном экземпляре
```bash
docker compose up -d --build
```

2. Запуск всех сервисов из `docker-compose.yml` в единственном экземпляре, кроме `API Trader` (запускается в нескольких экземплярах инструментами **docker-compose**)
```bash
docker compose up -d --build --scale api_trader=3
```
## Код-стайл

```bash
uv run ruff format .
uv run ruff check . --fix
```

## Настройка окружения

С помощью [UV](https://docs.astral.sh/uv/)
```bash
uv sync
```

С помощью pip
```bash
pip install -r requirements.txt
```