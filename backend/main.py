from fastapi import FastAPI, HTTPException
from backend import database, models, number_plate_recognition
import sqlite3
from datetime import datetime
import os

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    database.create_tables()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Parking Automation API"}

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
    video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "videos", "your_video.mp4")
    number_plate = number_plate_recognition.extract_number_plate(video_path)
    if number_plate:
        return {"number_plate": number_plate}
    else:
        raise HTTPException(status_code=404, detail="Number plate not found")