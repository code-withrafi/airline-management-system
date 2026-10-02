from sqlalchemy import text

from app.config.database import engine


def test_database_connection():

    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT 1")
        )

        print(
            "Database result:",
            result.scalar()
        )


if __name__ == "__main__":

    test_database_connection()