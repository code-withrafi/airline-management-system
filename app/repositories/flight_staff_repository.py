from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import Session

from app.models import (
    FlightStaff,
    Staff,
)



class FlightStaffRepository:
    """
    Repository responsible for database operations
    related to flight staff assignments.
    """


    def __init__(
        self,
        session: Session,
    ):

        self.session = session



    def get_all(
        self,
    ) -> list[FlightStaff]:

        statement = (
            select(FlightStaff)
            .order_by(
                FlightStaff.assigned_at.desc()
            )
        )


        return list(
            self.session
            .scalars(statement)
            .all()
        )



    def get_by_id(
        self,
        assignment_id: int,
    ) -> FlightStaff | None:


        statement = (
            select(FlightStaff)
            .where(
                FlightStaff.id
                ==
                assignment_id
            )
        )


        return self.session.scalar(
            statement
        )



    def get_by_flight_and_staff(
        self,
        flight_id: int,
        staff_id: int,
    ) -> FlightStaff | None:


        statement = (
            select(FlightStaff)
            .where(
                FlightStaff.flight_id
                ==
                flight_id,

                FlightStaff.staff_id
                ==
                staff_id,
            )
        )


        return self.session.scalar(
            statement
        )



    def get_by_flight(
        self,
        flight_id: int,
    ) -> list[FlightStaff]:


        statement = (
            select(FlightStaff)
            .where(
                FlightStaff.flight_id
                ==
                flight_id
            )
            .order_by(
                FlightStaff.assigned_at.asc()
            )
        )


        return list(
            self.session
            .scalars(statement)
            .all()
        )



    def create(
        self,
        *,
        flight_id: int,
        staff_id: int,
        assigned_role,
    ) -> FlightStaff:


        assignment = FlightStaff(
            flight_id=flight_id,
            staff_id=staff_id,
            assigned_role=assigned_role,
        )


        self.session.add(
            assignment
        )


        self.session.flush()


        return assignment



    def delete(
        self,
        assignment: FlightStaff,
    ) -> None:


        self.session.delete(
            assignment
        )


        self.session.flush()



    def count_by_flight(
        self,
        flight_id: int,
    ) -> int:


        statement = (
            select(
                func.count(
                    FlightStaff.id
                )
            )
            .where(
                FlightStaff.flight_id
                ==
                flight_id
            )
        )


        return (
            self.session.scalar(
                statement
            )
            or 0
        )