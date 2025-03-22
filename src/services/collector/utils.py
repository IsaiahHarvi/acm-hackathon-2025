import os

import psycopg2


def get_postgres_connection():
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        database=os.getenv("PG_DATABASE", "weather_db"),
        user=os.getenv("PG_USER", "admin"),
        password=os.getenv("PG_PASSWORD", "password"),
        port=os.getenv("PG_PORT", "5432"),
    )
    return conn
