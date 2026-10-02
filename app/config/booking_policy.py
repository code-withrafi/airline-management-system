"""
Central configuration for booking lifecycle rules.

A booking created with status UNPAID holds a seat for
PAYMENT_WINDOW. If it is still UNPAID after that window
(plus a small grace period), it is automatically cancelled
and the seat is released back to the pool.

All the times here are timedeltas so callers can do
arithmetic directly.
"""
from datetime import timedelta


# How long an UNPAID booking holds a seat.
PAYMENT_WINDOW = timedelta(minutes=15)

# Extra grace on top of PAYMENT_WINDOW. A payment submitted
# at T+14:59 on a slow connection still succeeds.
PAYMENT_GRACE = timedelta(seconds=30)

# Total time before a booking is considered expired.
EXPIRY_THRESHOLD = PAYMENT_WINDOW + PAYMENT_GRACE

# How often the background sweeper checks for expired bookings.
SWEEP_INTERVAL_SECONDS = 60
