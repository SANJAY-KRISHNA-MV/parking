from pydantic import BaseModel
from typing import Optional

class ParkingRecord(BaseModel):
    number_plate: str
    entry_time: str
    exit_time: Optional[str] = None
    slot_number: Optional[int] = None

class SlotStatus(BaseModel):
    slot_number: int
    is_available: bool