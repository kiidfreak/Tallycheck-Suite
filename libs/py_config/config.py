import os
from typing import Type, Union


class DevConfig:
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL")  # type: ignore[assignment]


class ProdConfig:
    DEBUG: bool = False
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL")  # type: ignore[assignment]


def get_config() -> Type[Union[DevConfig, ProdConfig]]:
    debug: bool = os.environ.get("FLASK_DEBUG", "0") == "1"
    return DevConfig if debug else ProdConfig
