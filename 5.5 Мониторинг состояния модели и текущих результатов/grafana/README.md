# Grafana

## Полезные ссылки
- [Официальные образы в Docker Hub](https://hub.docker.com/r/grafana/grafana)
- [Официальная документация](https://grafana.com/docs/grafana/latest/)

## Запуск контейнера
```bash
docker run \
    --name grafana-container \
    --network monitoring-net \
    -p 3000:3000 \
    -e GF_SECURITY_ADMIN_USER=admin \
    -e GF_SECURITY_ADMIN_PASSWORD=admin \
    -v <локальный путь к папке с данными графаны>/grafana_data:/var/lib/grafana \
    grafana/grafana
```

## Описание команды докера
- Флаг `--name grafana-container` позволяет обращаться к контейнеру по имени, вместо IP-адреса, внутри виртуальной сети докера
- Флаг `--network monitoring-net` запускает контейнер внутри виртуальной сети докера. Благодаря этому контейнеры, запущенные в одной виртуальной сети, смогут видеть друг друга
- Флаг `-p 3000:3000` пробрасывает дефолтный 3000 порт графаны наружу. Рекомендуется, в целях безопасности, изменить на нестандартный
- Переменные окружения `GF_SECURITY_ADMIN_USER` и `GF_SECURITY_ADMIN_PASSWORD` задают логин и пароль для учётной записи администратора
- Флаг `-v <локальный путь к папке с данными графаны>/grafana_data:/var/lib/grafana` маппит локальное хранилище с хранилищем контейнера. Благодаря этому, при перезапуске контейнера данные не потеряются