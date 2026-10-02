from app.services.seat_generator import (
    SeatGenerator,
)

from app.models import (
    SeatClass,
    SeatPosition,
)


def test_generate_seats():

    seats = SeatGenerator.generate(
        10
    )

    assert len(seats) == 10

    assert (
        seats[0]["seat_number"]
        ==
        "1A"
    )

    assert (
        seats[0]["position"]
        ==
        SeatPosition.WINDOW
    )

    assert (
        seats[0]["seat_class"]
        ==
        SeatClass.BUSINESS
    )


def test_large_aircraft_generation():

    seats = SeatGenerator.generate(
        180
    )

    assert len(seats) == 180


def test_generate_single_seat():

    seats = SeatGenerator.generate(
        1
    )

    assert len(seats) == 1

    assert (
        seats[0]["seat_number"]
        ==
        "1A"
    )


def test_generate_zero_capacity():

    seats = SeatGenerator.generate(
        0
    )

    assert len(seats) == 0


def test_generate_large_aircraft():

    seats = SeatGenerator.generate(
        500
    )

    assert len(seats) == 500