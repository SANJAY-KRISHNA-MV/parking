import sqlite3
from pathlib import Path

DATABASE_DIR = Path(__file__).resolve().parent.parent / "database"
DATABASE_FILE = DATABASE_DIR / "parking.db"

def create_connection():
    """Creates a database connection."""
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        print(f"Connected to SQLite database: {DATABASE_FILE}")
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_tables():
    """Creates the parking_records table."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parking_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number_plate TEXT NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT,
                    slot_number INTEGER
                );
            """)
            conn.commit()
            print("Parking records table created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    create_tables()