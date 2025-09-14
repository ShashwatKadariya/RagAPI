from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.schemas.booking import BookingCreate
from app.core.database import get_db

class BookingService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        
    ### Create a new booking
    def create_booking(self, booking: BookingCreate) -> Booking:
        db_booking = Booking(
            name=booking.name,
            email=booking.email,
            date=booking.date,
            time=booking.time
        )
        
        self.db.add(db_booking)
        self.db.commit()
        self.db.refresh(db_booking)
        
        return db_booking
    
    ### Get all bookings
    def get_bookings(self) -> List[Booking]:
        return self.db.query(Booking).all()
