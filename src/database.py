import psycopg2
import os

def connect_db():
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="sourabh",
        password=os.getenv("DB_PASSWORD"),
        host="localhost",
        port="5432"
    )
    return conn
