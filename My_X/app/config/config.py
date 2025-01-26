import logging
import os

import sentry_sdk
from pydantic_settings import BaseSettings, SettingsConfigDict
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration


class Settings(BaseSettings):
    """
    Configuration class for application settings.

    This class uses `pydantic.BaseSettings` to manage environment variables
    and application configurations. It also provides a property to construct
    the database URL dynamically.

    Attributes:
        DB_HOST (str): Hostname for the database.
        DB_PORT (int): Port number for the database.
        DB_NAME (str): Name of the database.
        DB_USER (str): Username for the database.
        DB_PASSWORD (str): Password for the database.
        SENTRY_DSN (str): Sentry DSN for error tracking.
        UPL_DIR (str): Directory for uploading media files.
        SAVE_PATH (str): Path where uploaded files will be saved.
        model_config (SettingsConfigDict): Configuration for loading environment variables.

    Properties:
        db_url (str): The complete database connection URL.

    Configuration:
        - Environment variables are loaded from a `.env` file located two directories
          above the current file.
        - Environment file encoding is set to UTF-8.
        - Additional unknown environment variables are ignored.
    """

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    SENTRY_DSN: str
    UPL_DIR: str
    SAVE_PATH: str
    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"
        ),
        env_file_encoding="utf8",
        extra="ignore",
    )

    @property
    def db_url(self) -> str:
        """
        Construct the database URL based on the provided configuration.

        Returns:
            str: The database connection URL in the format:
                 `postgresql+asyncpg://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>`.
        """
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings: Settings = Settings()  # type: ignore

logger: logging.Logger = logging.getLogger("app")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
    integrations=[
        sentry_logging,
        StarletteIntegration(
            transaction_style="endpoint",
            failed_request_status_codes={*range(400, 599)},
        ),
        FastApiIntegration(
            transaction_style="endpoint",
            failed_request_status_codes={*range(400, 599)},
        ),
    ],
)
