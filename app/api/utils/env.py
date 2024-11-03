from typing import Optional
import os
import dotenv
from app.config import EnvironmentConfig


def get_env(key: str, default: Optional[str] = None) -> str | None:
    value = os.environ.get(key)

    if value is None:
        return default

    return value


def set_env(key: str, value: str) -> None:
    os.environ[key] = value


def write_env(keys: list[str]) -> None:
    """
    Write the keys to the .env file
    """

    # Update env file with keys
    current_values = dotenv.dotenv_values(EnvironmentConfig.ENVIRONMENT_PATH)
    current_values.update({key: get_env(key) for key in keys})

    # Open the file in write mode
    with open(EnvironmentConfig.ENVIRONMENT_PATH, "w") as file:
        for key, value in current_values.items():
            file.write(f"{key}={value}\n")
