import psycopg2
import os
from dotenv import load_dotenv
load_dotenv() 


def connect_db():
    password = os.getenv("DB_PASSWORD") 
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="sourabh",
        password=password,
        host="localhost",
        port="5432"
    )
    return conn
