import os
import psycopg2
from dotenv import load_dotenv

load_dotenv() 

def get_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
    except Exception as error:
        print(f"Error connecting to the database: {error}")
        return None
    
