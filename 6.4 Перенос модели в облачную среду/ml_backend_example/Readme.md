# Пример простого бэкенд сервиса для инференса ML модели

Запуск сервиса из консоли
```shell
python main.py
```
Обратите внимание что нужны переменные окружения `PORT` и `MODEL_PATH`

Можно раскомментировать [эти строчки](main.py#L104), чтобы не задавать переменные окружения при запуске в консоли

Запуск сервиса в докере
```shell
docker build -t text_embedder:latest .

docker run -v /local/path/to/model:/home/python/app/models -e PORT=7777 -e MODEL_PATH=./models -p 7777:7777 text_embedder:latest
```

У сервиса есть middleware для сбора метрик

Есть несколько эндпоинтов:
- `GET /metrics` - отдаёт метрики в формате Prometheus
- `POST /embeds` - принимает на вход текст и возвращает эмбеддинги текста
- `GET /healthcheck` - (опционально) можно использовать для проверки того, жив контейнер или нет

Всё, что находится в [функции](main.py#L51) `lifespan` выполняется при запуске сервиса - пока не выполнится сервис будет недоступен

Пример запроса для `/embeds`
```shell
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '{"text": "some_text"}' https://<HOST>:<PORT>/embeds
```

Хедер с авторизацией нужен для Яндекс.Облака, в остальных случаях он не требуется