from pydantic import BaseModel
from typing import List, Optional, Union

class AppointmentSlot(BaseModel):
    start_time: str # ISO 8601 string

class Doctor(BaseModel):
    id: str
    name: str
    address: str
    speciality: Union[str, List[str]]
    insurance: List[str]
    slots: List[str] # List of ISO strings for simplicity in JSON
    booking_url: str = "" # for simplicity in JSON
    show_time: bool = True # Whether to show the time in the dashboard
