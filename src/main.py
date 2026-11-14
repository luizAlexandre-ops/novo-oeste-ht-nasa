from .database import get_connection

def main():
    connection = get_connection()
    
    if connection is None:
        print("Failed to connect to the database.")

    try:
        cursor = connection.cursor()

        cursor.execute("SELECT version();")
        result = cursor.fetchone()

        print(f"Database version: {result[0]}")
        cursor.close()

    except Exception as e:
        print(f"Error executing query: {e}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    main()