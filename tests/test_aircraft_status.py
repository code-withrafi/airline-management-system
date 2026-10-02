from app.models import AircraftStatus


def test_status_enum_values():

    assert (
        AircraftStatus.ACTIVE.value
        ==
        "ACTIVE"
    )


    assert (
        AircraftStatus.MAINTENANCE.value
        ==
        "MAINTENANCE"
    )


    assert (
        AircraftStatus.INACTIVE.value
        ==
        "INACTIVE"
    )