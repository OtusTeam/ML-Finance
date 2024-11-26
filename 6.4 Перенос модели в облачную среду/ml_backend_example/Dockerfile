FROM python:3.12

# Копируем requirements чтобы потом настроить виртуальное окружение
COPY requirements.txt .

# Обновляем систему, ставим зависимости для проекта,
# создаём пользователя и группу
RUN set -ex \
    && apt update \
    && apt install \
    && pip install -r requirements.txt --no-cache-dir \
    && apt --yes autoremove \
    && apt --yes clean \
    && groupadd -g 1001 python \
    && useradd --no-log-init -u 1001 -g python python

# Задаем рабочую директорию
RUN mkdir -p /home/python/ && chown -R python:python /home/python/
WORKDIR /home/python/app/
# Копируем все нужные файлы в образ
COPY --chown=python:python . .

# Активируем пользователя
USER python

# Запускаем сервис
CMD ["python", "main.py"]