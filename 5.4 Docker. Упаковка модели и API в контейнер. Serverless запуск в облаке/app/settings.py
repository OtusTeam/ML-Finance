import json
import logging
import logging.handlers
import os
import sys
import time
import typing
from datetime import UTC, datetime

import pydantic
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Trading Service"
    APP_VERSION: str = "1.0.0"

    HOST: str = pydantic.Field("0.0.0.0")
    PORT: int = pydantic.Field("7777")

    T_SANDBOX_TOKEN: pydantic.SecretStr = pydantic.Field("")

    class Config:
        env_file = ".env"


class JsonFormatter(logging.Formatter):
    """Форматер, который преобразует запись лога в JSON-строку."""

    def __init__(self, fmt=None, datefmt=None, style="%"):
        super().__init__(fmt, datefmt, style)
        self.converter = time.gmtime  # используем UTC+0 время, независимо от локального часового пояса

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.module,
            "line": record.lineno,
            "function": record.funcName,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def setup_logging(log_dir: str = "logs"):
    """Настраивает логирование с выводом в консоль (JSON) и в файл (ежедневная ротация).

    Args:
        log_dir: Директория для хранения лог-файлов.

    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 1. Основной логер
    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # 2. Обработчик для консоли (stdout)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(JsonFormatter())

    # 3. Обработчик для файла с ежедневной ротацией
    current_date = datetime.now(tz=UTC).strftime("%Y-%m-%d")
    file_path = os.path.join(log_dir, f"trading_bot-{current_date}.log")

    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=file_path,
        when="midnight",
        interval=1,
        backupCount=7,  # Храним логи за последние 7 дней
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)

    # 4. Добавляем обработчики к логеру
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)

    return logger


LOGGER: typing.Final = setup_logging()
settings: typing.Final = Settings()
