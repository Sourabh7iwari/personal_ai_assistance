import psycopg2

def connect_db():
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="sourabh",
        password="sourabhsuperpassword",
        host="localhost",
        port="5432"
    )
    return conn
