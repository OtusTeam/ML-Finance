# Пример docker compose для поднятия Prometheus и Grafana

Запуск сервисов
```shell
docker compose up
```
Обратите внимание что в `docker-compose.yml` необходимо указать свои локальные пути в монтировании томов (для [grafana](docker-compose.yml#L17), для [prometheus](docker-compose.yml#L6))

В файле конфигов для prometheus раздел [remote_write](prometheus/prometheus.yaml#L13) опционален. Он используется для прокидывания метрик в Яндекс.Облако