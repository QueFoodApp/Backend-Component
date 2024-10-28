import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DB_HOST = os.getenv("HOST")
DB_PORT = os.getenv("PORT")
DB_NAME = os.getenv("DATABASE")
DB_USER = os.getenv("USER")
DB_PASSWORD = os.getenv("PASSWORD")

print(f"Connecting to database with the following settings:")
print(f"Host: {DB_HOST}")
print(f"Database: {DB_NAME}")
print(f"User: {DB_USER}")
print(f"Password: {DB_PASSWORD}")  # Be careful: this should not be printed in production


def get_db():
    if not DB_USER == "developuser":
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user="developuser",
            password=DB_PASSWORD,
            port=DB_PORT
    )
    else:
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
    )
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
        connection.close()