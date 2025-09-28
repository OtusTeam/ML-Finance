FROM python:3.13

# Обновляем систему, создаём пользователя и группу
RUN set -ex \
    && apt update \
    && apt install \
    && pip install uv \
    && apt --yes autoremove \
    && apt --yes clean \
    && groupadd -g 1001 python \
    && useradd --no-log-init -u 1001 -g python python \
    && mkdir -p /home/python/ \
    && chown -R python:python /home/python/

# Задаем рабочую директорию
WORKDIR /home/python/app/

# Копируем файлы зависимостей uv
COPY pyproject.toml uv.lock ./

# Синхронизируем зависимости (установка строго по uv.lock)
RUN uv sync --frozen --no-cache --no-dev

# Копируем все нужные файлы в образ
COPY --chown=python:python . .

# Активируем пользователя
USER python

# Запускаем сервис
CMD ["/home/python/app/.venv/bin/python", "main.py"]