import psycopg
from psycopg.rows import dict_row
from psycopg.sql import SQL

DB_PARAMS = {
    'dbname' : 'memory_agent',
    'user' : 'example_user',
    'password' : 'user',
    'host': 'localhost',
    'port':'5432'
}

def connect_db():
    conn = psycopg.connect(**DB_PARAMS) 
    return conn

def fetch_conversations():
    conn = connect_db()
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute('SELECT * FROM conversations') 
        conversations = cursor.fetchall()
    conn.close()
    return conversations

def store_conversations(prompt, response):
    conn = connect_db()
    with conn.cursor() as cursor:
        query = SQL(
            "INSERT INTO conversations (timestamp, prompt, response) VALUES (CURRENT_TIMESTAMP, %s, %s)"
        )
        cursor.execute(query, (prompt, response))
        conn.commit() 
    conn.close() 

def remove_last_conversation():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute('DELETE FROM conversations WHERE id = SELECT MAX(id) FROM conversations')
        cursor.commit()
    conn.close()

    