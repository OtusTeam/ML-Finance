# Работа с Yandex Cloud

1. Устанавливаем консольную утилиту `yc`

    [Инструкции](https://yandex.cloud/ru/docs/cli/quickstart#install) для Linux, macOS, Windows

2. Регистрируемся и создаём платёжный аккаунт на [cloud.yandex.ru](https://yandex.cloud/ru/)

3. Создаём сервисный аккаунт, который будут использовать наши сервисы.

    [Инструкция](https://yandex.cloud/ru/docs/iam/operations/sa/create) по созданию сервисного аккаунта

## Работа с Object Storage

1. Создадим **Yandex Object Storage**

    [Интсрукция](https://yandex.cloud/ru/docs/storage/quickstart?from=int-console-help-center-or-nav) по созданию

2. Назначим нужные нам роли для сервисного аккаунта. В нашем примере это роль `storage.admin`, но можно `storage.uploader` и `storage.viewer`.

    Для этого перейдем в наше **Object Storage**, в пункте *Безопасность* нажмём *Назначить роли*, выберем наш сервисный аккаунт и добавим необходимые роли

    Более подробная [инструкция](https://yandex.cloud/ru/docs/storage/operations/buckets/iam-access) по назначению ролей для **Object Storage**

3. Теперь в консоли в *Object Storage -> Объекты* можно загружать файлы

## Работа с контейнерами

1. Создадим **Yandex Container Registry**

    [Инструкция](https://yandex.cloud/ru/docs/container-registry/quickstart/?from=int-console-help-center-or-nav) по созданию

2. Запушим в **Container Registry** наш docker image

    2.1. Получим наш OAuth-токен и залогинимся в **Container Registry** 

    ```shell
    echo <OAuth-токен> | docker login \
    --username oauth \
    --password-stdin \
    cr.yandex
    ```

    Обратите внимание, если работаете с докером через **sudo**, то и в логине надо использовать `... | sudo docker login ...`

    Более подробная [инструкция](https://yandex.cloud/ru/docs/container-registry/operations/authentication?from=int-console-help-center-or-nav)
    
    2.2. Для загрузки в **Yandex Container Registry** образу необходимо присвоить тег в формате `cr.yandex/<идентификатор_реестра>/<имя_Docker-образа>:<тег>`

    Создаём свой образ
    ```shell
    docker build -t cr.yandex/<идентификатор_реестра>/<имя_Docker-образа>:<тег>

    # Например
    docker build -t cr.yandex/crpffeshm5v5qg8m4rti/my_image:latest
    ```

    Либо меняем тег у готового
    ```shell
    docker tag <тег_исходного образа> cr.yandex/<идентификатор_реестра>/<имя_Docker-образа>:<тег>
    
    # Например
    docker tag hello-world:latest cr.yandex/crpffeshm5v5qg8m4rti/hello-world:latest
    ```

    2.3. Отправляем образ в **Container Registry**

    ```shell
    docker push <имя_образа>

    # Например
    docker push cr.yandex/crpffeshm5v5qg8m4rti/hello-world:latest
    ```

    Теперь можно зайти в **Yandex Container Registry** в консоли и увидеть наш образ

    Более подробные инструкции по [созданию](https://yandex.cloud/ru/docs/container-registry/operations/docker-image/docker-image-create) и [загрузке](https://yandex.cloud/ru/docs/container-registry/operations/docker-image/docker-image-push) образов

3. Загруженный образ можно развернуть несколькими способами: Kubernetes, serverless container, контейнер на виртуальной машине. 

    *Рассмотрим вариант с помощью **Serverless Container***
    
    1. Создаём контейнер в **Serverless Containers**

    2. Создаём новую ревизию контейнера. Задаём необходимые ресурсы, образ и сервисный акканут. При необходимости можно смонтировать бакет из **Object Storage** - очень удобно, если там хранятся какие-то тяжелые файлы. В таком случае образ будет легким, а файлы появятся при запуске контейнера.

    3. После создания ревизии контейнер будет готов к работе. В пункте *Обзор* контейнера будет *Ссылка для вызова* с URL-адресом, по которому можно обратиться к контейнеру

        Если пункт *Публичный контейнер* не включен, то в headers запроса необходимо будет передать IAM-токен в формате `Authorization: "Bearer <IAM-token>"`

        Более подробная [инструкция](https://yandex.cloud/ru/docs/serverless-containers/quickstart/container)

    *Рассмотрим вариант с помощью виртуальной машины*

    1. Перед началом создания виртуальной машины (ВМ) на своём устройстве необходимо сгенерировать приватный и публичный ssh ключ

    2. Создаём ВМ в **Compute Cloud** - выбираем нужную ОС, ресурсы, сервисный аккаунт и добавляем публичный ssh ключ

    3. Подключаемся по ssh к нашей ВМ. При подключении необходимо указать файл с приватным ssh ключом нашего устройства

        ```shell
        ssh -I <путь_к_приватному_ключу> <ip_виртуальной_машины>
        ```

    4. При необходимости устанавливаем все недостающие пакеты

    5. В ВМ так же можно смонтировать S3 бакет с помощью **FUSE**, но для этого нужны сторонние утилиты

        Устанавливаем `GeeseFS`, `s3fs`, `goofys` или `rclone`

        **Пример монтирования с помощью `GeeseFS` в Ubuntu:**

        Устанавливаем `FUSE`

        ```shell
        sudo apt-get install fuse
        ```

        Скачиваем и устанавливаем `GeeseFS`

        ```shell
        wget https://github.com/yandex-cloud/geesefs/releases/latest/download/geesefs-linux-amd64
        chmod a+x geesefs-linux-amd64
        sudo cp geesefs-linux-amd64 /usr/bin/geesefs
        ```

        Создаём статический API ключ для AWS ([инструкция](https://yandex.cloud/ru/docs/iam/concepts/authorization/access-key))

        Далее в файле `~/.aws/credentials` (если его нет, то создайте, например `mkdir -p ~/.aws/ && touch ~/.aws/credentials`) прописываем

        ```shell
        [default]
            aws_access_key_id=<идентификатор_ключа>
            aws_secret_access_key=<секретный_ключ>
        ```

        Обратите внимание, что при работе с `GeeseFS` через `sudo` система будет смотреть не в `~/.aws/credentials`, а в `/root/.aws/credentials`

        Монтируем наш S3 бакет к ВМ

        ```shell
        geesefs <имя_бакета> <точка_монтирования>

        # Например
        geesefs otus-bucket /home/user/s3
        ```

        Затем в файл `/etc/fuse.conf` добавьте или раскомментируйте строку

        ```shell
        user_allow_other
        ```

        **Внимание:** без этого параметра смонтированный бакет не получится подключить к докер контейнеру

        Для автоматического монтирования при запуске ВМ можно добавить в файл `/etc/fstab` следующую строку

        ```shell
        <имя_бакета>    <точка_монтирования>    fuse.geesefs    _netdev,allow_other,--file-mode=0666,--dir-mode=0777    0   0

        # Например
        otus-bucket    /home/user/s3    fuse.geesefs    _netdev,allow_other,--file-mode=0666,--dir-mode=0777    0   0
        ```

        Теперь можно прокинуть наш бакет в докер контейнер с помощью флагов `--volume` или `--mount`

        Более подробная [инструкция](https://yandex.cloud/ru/docs/storage/tools/geesefs) по `GeeseFS` и другим утилитам

    6. Логинимся в **Container Registry** (см. п. 2.1)

    7. Скачиваем наш образ

        ```shell
        docker pull <имя_образа>

        # Например
        docker pull cr.yandex/crpffeshm5v5qg8m4rti/hello-world:latest
        ```
    
    8. Запускаем контейнер с необходимыми настройками

        ```shell
        docker run <имя_образа>
        
        # Например
        docker run cr.yandex/crpffeshm5v5qg8m4rti/hello-world:latest
        ```

        Более подробная [инструкция](https://yandex.cloud/ru/docs/container-registry/tutorials/run-docker-on-vm/console)

## Работа с метриками

Базовые метрики контейнеров Яндекс Облако будет забирать автоматом и можно будет их посмотреть, однако, если мы хотим расширенный мониторинг, то необходимо самому настроить сбор метрик

Для метрик будем использовать **Prometheus** и **Grafana**

Можно вместо **Prometheus** использовать **Yandex Unified Agent**, но в таком случае мы залочимся на облако

Для того, чтобы **Prometheus** мог забирать метрики нам нужна ручка в нашем сервисе с моделью, поэтому добавим в веб-сервис ручку `/metrics`, откуда можно будет забирать метрики с помощью GET запроса

В Яндекс Облаке есть **Yandex Managed Service for Prometheus®**, который можно настроить для хранения метрик нашего **Prometheus**

Для этого необходимо создать Workspace и в файле настроек нашего **Prometheus** указать URL данного workspace для функции **Remote Write** и API ключ сервисного аккаунта.

[Инструкция](https://yandex.cloud/ru/docs/iam/operations/api-key/create) по получению API ключа

1. Создадим новую ВМ с сервисным аккаунтом

2. Для сервисного аккаунта надо добавить роли `monitoring.editor` и `monitoring.viewer`

    Заходим в *Identity and Access Management -> Права доступа -> Настроить доступ -> Выбираем сервисный аккаунт и добавляем роли*

3. Создадим файл с настройками для **Prometheus**

    *Пример promteheus.yml*
    ```yaml
    global:
      scrape_interval: 5s
      evaluation_interval: 5s

    scrape_configs:
      - job_name: 'embedder'  # Имя сервиса
          scrape_interval: 5s  # Можно переопределить глобальные настрокий
          metrics_path: /metrics  # ручка, откуда будем забирать метрики нашего сервиса
          static_configs:
            - targets: ['<HOST>:<PORT>']  # адрес сервиса, с которого будем забирать метрики

    remote_write:
      - url: "<yandex_cloud_prometheus_workspace_url>"
        bearer_token: "api_ключ_сервисного_аккаунта"
    ```
4. Добавим **Proemetheus** и **Grafana** в `docker-compose.yaml`

5. Запустим сервисы

    ```shell
    docker compose up
    ```

    Теперь **Prometheus** и **Grafana** доступны по IP нашей ВМ и соответствующему порту. 

    Также **Prometheus** будет транслировать метрики в Яндекс.Облако

## Работа с логами

Логи от **Serverless Container** будут собираться автоматически и попадать в **Cloud Logging**

Для пересылки логов из ВМ в **Cloud Logging** понадобится **FluentBit** с плагином от Яндекса.

Подробная [инструкция](https://yandex.cloud/ru/docs/tutorials/security/vm-fluent-bit-logging)

В качестве альтернативы можно сохранять логи докера в файл на S3

```shell
docker logs -f [container_id] > [path_to_mounted_s3]/logs.log

# Например
docker logs -f d8453812a556 > /home/user/s3/logs.log
```

## Масштабирование

**Serverless Container** будут масштабироваться автоматически на количество подготовленных ревизий ([подробнее](https://yandex.cloud/ru/docs/serverless-containers/operations/scaling-settings-add))

Для виртуальных машин можно создать группу с автоматической балансировкой ([инструкция](https://yandex.cloud/ru/docs/compute/tutorials/vm-autoscale/console)) или по расписанию ([инструкция](https://yandex.cloud/ru/docs/compute/tutorials/vm-scale-scheduled/console)) или для очередей ([инструкция](https://yandex.cloud/ru/docs/compute/tutorials/autoscale-monitoring))