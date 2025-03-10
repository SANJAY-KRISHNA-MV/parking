import sqlite3
from pathlib import Path
from datetime import datetime

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

def insert_parking_record(number_plate, entry_time=None):
    """Inserts a new parking record into the database."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            if entry_time is None:
                entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Use current time if not provided
            cursor.execute("INSERT INTO parking_records (number_plate, entry_time) VALUES (?, ?)", (number_plate, entry_time))
            conn.commit()
            print(f"Parking record inserted for {number_plate} at {entry_time}")
        except sqlite3.Error as e:
            print(f"Error inserting parking record: {e}")
        finally:
            conn.close()

def update_parking_record(number_plate, exit_time=None):
    """Updates the exit_time for an existing parking record."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            if exit_time is None:
                exit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Use current time if not provided
            cursor.execute("UPDATE parking_records SET exit_time = ? WHERE number_plate = ?", (exit_time, number_plate))
            conn.commit()
            print(f"Parking record updated for {number_plate} with exit time {exit_time}")
        except sqlite3.Error as e:
            print(f"Error updating parking record: {e}")
        finally:
            conn.close()

def get_entry_record(number_plate):
    """
    Retrieves the entry record for a given number plate from the database.
    Returns the record with the given number plate that has an entry time but no exit time.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parking_records WHERE number_plate = ? AND exit_time IS NULL", (number_plate,))
            row = cursor.fetchone()
            if row:
                return {'id': row[0], 'number_plate': row[1], 'entry_time': row[2], 'exit_time': row[3], 'slot_number': row[4]}
            else:
                return None
        except sqlite3.Error as e:
            print(f"Error retrieving entry record: {e}")
            return None
        finally:
            conn.close()

# Example usage (optional):
if __name__ == "__main__":
    create_tables()
    insert_parking_record("MH 12 AB 1234")
    update_parking_record("MH 12 AB 1234")