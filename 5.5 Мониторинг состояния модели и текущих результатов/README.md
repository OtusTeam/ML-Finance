# Мониторинг состояния модели и текущих результатов. Prometheus, Grafana, Alertmanager

## Краткое описание:
Необходимо запустить 5 контейнеров:
- [Prometheus](prometheus/README.md)
- [Grafana](grafana/README.md)
- [Alertmanager](alertmanager/README.md)
- [ML signals analysis](app/)
- [Trading bot](../5.4%20Docker.%20Упаковка%20модели%20и%20API%20в%20контейнер.%20Serverless%20запуск%20в%20облаке/README.md)

Все контейнеры должны быть запущены в одной виртуальной сети, чтобы могли взаимодействовать друг с другом

#### Схема взаимодействия контейнеров
- Контейнер `ML signals analysis` каждые 60 секунд запрашивает рыночные данные у `Trading bot` по ручке `/trading/get_market_data`
- Контейнер `ML signals analysis` рассчитывает сигнал на основе полученных рыночных данных
- Если сигнал `BUY` или `SELL`, то контейнер `ML signals analysis` отправляет запрос к `Trading bot` на исполнение сигнала по ручке `/trading/execute_trade`
- Контейнер `Prometheus` регулярно забирает метрики у сервиса `ML signals analysis` по ручке `/metrics`
- В контейнер `Grafana` настраивается новый источник данных - контейнер `Prometheus`
- Контейнер `Prometheus`, при возникновении алертов, отправляет их в контейнер `Alertmanager`
- Контейнер `Alertmanager` отправляет полученные алерты в `Telegeram`

#### Создать виртуальную сеть для докера
```bash
docker network create monitoring-net
```

#### Запустить `Trading bot` в виртуальной сети
Перейти в [папку проекта](../5.4%20Docker.%20Упаковка%20модели%20и%20API%20в%20контейнер.%20Serverless%20запуск%20в%20облаке/) и собрать образ
```bash
docker build -t trader .
```

Запустить контейнер
```bash
docker run \
    --name trader \
    --network monitoring-net \
    -p 1236:1236 \
    -v <локальный путь к папке с логами>/logs:/home/python/app/logs \
    --env-file <локальный путь к env файлу>.env \
    trader
```

#### Запустить `ML signals analysis` в виртуальной сети
Перейти в [папку проекта](../5.5%20Мониторинг%20состояния%20модели%20и%20текущих%20результатов/) и собрать образ
```bash
docker build -t ml-signals .
```

Запустить контейнер
```bash
docker run \
    --name ml-signals \
    --network monitoring-net \
    -p 7777:7777 \
    -v <локальный путь к папке с моделями>/chronos-t5-tiny/:/home/python/app/models/chronos-t5-tiny \
    -v <локальный путь к папке с логами>/logs:/home/python/app/logs \
    --env-file <локальный путь к env файлу>.env \
    ml-signals
```

Инструкции по запуску остальных сервисов см. в Readme в соответствующих папках

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