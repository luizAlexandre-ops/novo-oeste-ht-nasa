from experiments.leagacy.database import get_connection

def main() -> None:
    connection = get_connection()
    
    if connection is None:
        print("Failed to connect to the database.")
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            print(f"Database version: {cursor.fetchone()[0]}")
    except Exception as e:
        print(f"Error executing query: {e}")
    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    main()
