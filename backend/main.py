from fastapi import FastAPI, HTTPException
from backend import database, models, number_plate_recognition
import sqlite3
from datetime import datetime
import os
import json

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    database.create_tables()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Parking Automation API"}

@app.get("/api/slots") #<-- Add this endpoint
async def get_slots():
    # Load your parking layout
    with open("parking_layout.json", "r") as f:
        parking_layout = json.load(f)

    # Load your image and process it.
    image_path = "../videos/parking_layout_setup.jpg" #or whatever your image path is.
    from slot_management import process_image #adjust the import.
    slots_data = process_image(image_path)

    # Convert the slot data to a format that can be returned as JSON.
    return slots_data

@app.post("/parking_records/", response_model=models.ParkingRecord)
async def create_parking_record(record: models.ParkingRecord):
    conn = database.create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO parking_records (number_plate, entry_time) VALUES (?, ?)
        """, (record.number_plate, record.entry_time))
        conn.commit()
        record_id = cursor.lastrowid
        cursor.execute("SELECT * FROM parking_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        return models.ParkingRecord(number_plate=row[1], entry_time=row[2], exit_time=row[3], slot_number=row[4])
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/parking_records/{record_id}", response_model=models.ParkingRecord)
async def update_parking_record(record_id: int, exit_time: str):
    conn = database.create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE parking_records SET exit_time = ? WHERE id = ?
        """, (exit_time, record_id))
        conn.commit()
        cursor.execute("SELECT * FROM parking_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Record not found")
        return models.ParkingRecord(number_plate=row[1], entry_time=row[2], exit_time=row[3], slot_number=row[4])
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/extract_plate/")
async def extract_plate():
    """
    Extracts the number plate from the video and stores it in the database.
    """
    video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "videos", "entry_capture_feed.mp4")
    number_plate = number_plate_recognition.extract_number_plate(video_path)
    if number_plate:
        entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Capture the entry time
        database.insert_parking_record(number_plate, entry_time)  # Insert the record
        return {"number_plate": number_plate, "entry_time": entry_time}
    else:
        raise HTTPException(status_code=404, detail="Number plate not found")
    
@app.post("/process_exit/")
async def process_exit():
    """
    Processes the exit of a vehicle and updates the database.
    """
    video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "videos", "exit_camera_feed.mp4")  # Adjust the path as needed
    number_plate = number_plate_recognition.extract_number_plate(video_path)
    if number_plate:
        try:
            # Fetch the entry record from the database
            entry_record = database.get_entry_record(number_plate)  # You'll need to implement this function in database.py
            if entry_record:
                exit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                entry_time = entry_record.get('entry_time')  # Extract the entry time from the record

                # Update exit time in the database
                database.update_parking_record(number_plate, exit_time)
                
                return {"number_plate": number_plate, "entry_time": entry_time, "exit_time": exit_time}  # Include entry and exit times in the response
            else:
                return {"message": f"No entry record found for {number_plate}."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process exit: {e}")
    else:
        raise HTTPException(status_code=404, detail="Number plate not found")