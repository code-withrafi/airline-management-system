# api/main.py — updated
import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth, flights, seats, bookings, payments, passengers
from app.config.booking_policy import SWEEP_INTERVAL_SECONDS
from app.config.database import SessionLocal
from app.services.booking_service import BookingService


logger = logging.getLogger("booking_sweeper")


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


async def _sweep_loop() -> None:
    """Run the expiry sweep on a fixed interval, forever."""

    while True:
        try:
            await asyncio.sleep(SWEEP_INTERVAL_SECONDS)
            expired = await _sweep_expired_bookings_once()
            if expired:
                logger.info(
                    "Expired %d unpaid booking(s).", expired
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Booking sweeper iteration failed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_sweep_loop())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title="Airline Passenger API",
    version="0.2.0",
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
app.include_router(flights.router,    prefix="/api/flights",    tags=["flights"])
app.include_router(seats.router,      prefix="/api",            tags=["seats"])
app.include_router(bookings.router,   prefix="/api/bookings",   tags=["bookings"])
app.include_router(payments.router,   prefix="/api/payments",   tags=["payments"])
app.include_router(passengers.router, prefix="/api/passengers", tags=["passengers"])


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}