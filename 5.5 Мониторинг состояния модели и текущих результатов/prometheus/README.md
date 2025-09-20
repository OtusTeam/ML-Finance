# Prometheus

## Полезные ссылки
- [Официальные образы в Docker Hub](https://hub.docker.com/r/prom/prometheus)
- [Официальная документация](https://prometheus.io/docs/introduction/overview/)


## Запуск контейнера
```bash
docker run \
    --name prometheus-container \
    --network monitoring-net \
    -p 9090:9090 \
    -v <локальный путь к папке с данными прометеуса>/prometheus_data:/prometheus \
    -v <локальный путь к файлу настроек прометеуса>/prometheus.yml:/etc/prometheus/prometheus.yml \
    -v <локальный путь к файлу настроек уведомлений>/alert_rules.yml:/etc/prometheus/alert_rules.yml \
    prom/prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/prometheus
```

## Описание команды докера
- Флаг `--name prometheus-container` позволяет обращаться к контейнеру по имени, вместо IP-адреса, внутри виртуальной сети докера
- Флаг `--network monitoring-net` запускает контейнер внутри виртуальной сети докера. Благодаря этому контейнеры, запущенные в одной виртуальной сети, смогут видеть друг друга
- Флаг `-p 9090:9090` пробрасывает дефолтный 9090 порт прометеуса наружу. Рекомендуется, в целях безопасности, изменить на нестандартный
- Флаг `-v <локальный путь к папке с данными прометеуса>/prometheus_data:/prometheus` маппит локальное хранилище с хранилищем контейнера. Благодаря этому, при перезапуске контейнера данные не потеряются
- Флаг `-v <локальный путь к файлу настроек прометеуса>/prometheus.yml:/etc/prometheus/prometheus.yml` пробрасывает настройки прометеуса внутрь контейнера
- Флаг `-v <локальный путь к файлу настроек уведомлений>/alert_rules.yml:/etc/prometheus/alert_rules.yml` пробрасывает правила уведомлений для Alertmanager
- Флаг `--config.file=/etc/prometheus/prometheus.yml` указывает путь к файлу настроек внутри контейнера
- Флаг `--storage.tsdb.path=/prometheus` указывает путь к папке, в которой будут храниться все данные внутри контейнера

