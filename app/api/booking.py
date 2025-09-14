from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import BookingService

booking_router = APIRouter()

@booking_router.post("/", response_model=BookingResponse)
async def create_booking(
    booking: BookingCreate,
    booking_service: BookingService = Depends()
):
    try:
        return booking_service.create_booking(booking)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@booking_router.get("/", response_model=List[BookingResponse])
async def list_bookings(
    booking_service: BookingService = Depends()
):
    return booking_service.get_bookings()
