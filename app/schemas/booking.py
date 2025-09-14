from pydantic import BaseModel, EmailStr
from datetime import datetime

class BookingCreate(BaseModel):
    name: str
    email: EmailStr
    date: str
    time: str

class BookingResponse(BaseModel):
    id: int
    name: str
    email: str
    date: str
    time: str
    created_at: datetime
    
    class Config:
        from_attributes = True
