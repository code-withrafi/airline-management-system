import os

from dotenv import load_dotenv


load_dotenv()


class Settings:

    APP_NAME = os.getenv(
        "APP_NAME",
        "Airline Management System"
    )

    APP_ENV = os.getenv(
        "APP_ENV",
        "development"
    )

    DB_HOST = os.getenv(
        "DB_HOST",
        "localhost"
    )

    DB_PORT = os.getenv(
        "DB_PORT",
        "5432"
    )

    DB_NAME = os.getenv(
        "DB_NAME",
        "airline_management"
    )

    DB_USER = os.getenv(
        "DB_USER",
        "postgres"
    )

    DB_PASSWORD = os.getenv(
        "DB_PASSWORD",
        ""
    )

    @property
    def database_url(self) -> str:

        return (
            f"postgresql+psycopg://"
            f"{self.DB_USER}:"
            f"{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:"
            f"{self.DB_PORT}/"
            f"{self.DB_NAME}"
        )


settings = Settings()