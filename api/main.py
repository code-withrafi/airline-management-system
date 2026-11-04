# api/main.py — updated
import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import (
    auth,
    flights,
    seats,
    bookings,
    payments,
    passengers,
    ml,
    staff_auth,
    schedule,
)
from app.config.booking_policy import SWEEP_INTERVAL_SECONDS
from app.config.database import SessionLocal
from app.services.booking_service import BookingService
from app.services.flight_completion_service import FlightCompletionService


logger = logging.getLogger("background_sweeper")


# ==================================================================
# Booking sweeper — cancels UNPAID bookings past their payment window
# ==================================================================

async def _sweep_expired_bookings_once() -> int:
    """Cancel UNPAID bookings past their payment window.

    Runs in a worker thread because the underlying
    BookingService is sync SQLAlchemy.
    """

    def _run() -> int:
        session = SessionLocal()
        try:
            return BookingService(session).expire_unpaid_bookings()
        finally:
            session.close()

    return await asyncio.to_thread(_run)


async def _booking_sweep_loop() -> None:
    """Run the booking expiry sweep on a fixed interval, forever."""

    while True:
        try:
            await asyncio.sleep(SWEEP_INTERVAL_SECONDS)
            expired = await _sweep_expired_bookings_once()
            if expired:
                logger.info("Expired %d unpaid booking(s).", expired)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Booking sweeper iteration failed.")


# ==================================================================
# Flight completion sweeper — marks expired flights as COMPLETED
# ==================================================================

# How often to check for flights whose arrival time has passed (seconds)
FLIGHT_SWEEP_INTERVAL_SECONDS = 60


async def _complete_expired_flights_once() -> int:
    """Mark flights whose arrival time has passed as COMPLETED.

    Runs in a worker thread because the underlying service uses
    sync SQLAlchemy.
    """

    def _run() -> int:
        session = SessionLocal()
        try:
            return FlightCompletionService(session).complete_expired_flights()
        finally:
            session.close()

    return await asyncio.to_thread(_run)


async def _flight_sweep_loop() -> None:
    """Run the flight completion sweep on a fixed interval, forever."""

    while True:
        try:
            await asyncio.sleep(FLIGHT_SWEEP_INTERVAL_SECONDS)
            completed = await _complete_expired_flights_once()
            if completed:
                logger.info("Marked %d flight(s) as COMPLETED.", completed)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Flight completion sweeper iteration failed.")


# ==================================================================
# Lifespan — starts both sweepers, cancels them cleanly on shutdown
# ==================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    booking_task = asyncio.create_task(_booking_sweep_loop())
    flight_task = asyncio.create_task(_flight_sweep_loop())

    try:
        yield
    finally:
        booking_task.cancel()
        flight_task.cancel()

        with suppress(asyncio.CancelledError):
            await booking_task
        with suppress(asyncio.CancelledError):
            await flight_task


# ==================================================================
# FastAPI app
# ==================================================================

app = FastAPI(
    title="Airline Passenger API",
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,       prefix="/api/auth",       tags=["auth"])
app.include_router(staff_auth.router, prefix="/api/auth",       tags=["staff-auth"])
app.include_router(flights.router,    prefix="/api/flights",    tags=["flights"])
app.include_router(seats.router,      prefix="/api",            tags=["seats"])
app.include_router(bookings.router,   prefix="/api/bookings",   tags=["bookings"])
app.include_router(payments.router,   prefix="/api/payments",   tags=["payments"])
app.include_router(passengers.router, prefix="/api/passengers", tags=["passengers"])
app.include_router(ml.router,         prefix="/api/ml",         tags=["ml"])
app.include_router(schedule.router,   prefix="/api/schedule",   tags=["schedule"])


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}