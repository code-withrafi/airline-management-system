# app/validators/__init__.py
#
# Intentionally empty.
#
# Validators are imported directly by module path to avoid a
# circular import between validators and services:
#   from app.validators.flight_status_validator import FlightStatusValidator
#
