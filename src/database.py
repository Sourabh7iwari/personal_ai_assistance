import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()  # This should be at the top of your main application file


def connect_db():
    password = os.getenv("DB_PASSWORD")  # Ensure this prints the expected password
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="sourabh",
        password=password,
        host="localhost",
        port="5432"
    )
    return conn
