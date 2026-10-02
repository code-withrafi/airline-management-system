from sqlalchemy import (
    func,
    or_,
    select,
)

from sqlalchemy.orm import Session

from app.models import Staff



class StaffRepository:
    """
    Repository responsible for database operations
    related to staff.
    """


    def __init__(
        self,
        session: Session,
    ):

        self.session = session



    def get_all(
        self,
    ) -> list[Staff]:

        statement = (
            select(Staff)
            .order_by(
                Staff.employee_id.asc()
            )
        )


        return list(
            self.session
            .scalars(statement)
            .all()
        )



    def get_by_id(
        self,
        staff_id: int,
    ) -> Staff | None:


        statement = (
            select(Staff)
            .where(
                Staff.id == staff_id
            )
        )


        return self.session.scalar(
            statement
        )



    def get_by_employee_id(
        self,
        employee_id: str,
    ) -> Staff | None:


        normalized = (
            employee_id
            .strip()
            .upper()
        )


        statement = (
            select(Staff)
            .where(
                func.upper(
                    Staff.employee_id
                )
                ==
                normalized
            )
        )


        return self.session.scalar(
            statement
        )



    def search(
        self,
        search_text: str,
    ) -> list[Staff]:


        normalized_text = (
            search_text
            .strip()
        )


        if not normalized_text:

            return self.get_all()



        pattern = (
            f"%{normalized_text}%"
        )


        statement = (
            select(Staff)
            .where(
                or_(
                    Staff.employee_id.ilike(
                        pattern
                    ),

                    Staff.first_name.ilike(
                        pattern
                    ),

                    Staff.last_name.ilike(
                        pattern
                    ),

                    Staff.position.ilike(
                        pattern
                    ),
                )
            )
            .order_by(
                Staff.employee_id.asc()
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
        user_id: int,
        employee_id: str,
        first_name: str,
        last_name: str,
        phone: str,
        position: str,
    ) -> Staff:

        staff = Staff(
            user_id=user_id,
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            position=position,
        )

        self.session.add(staff)
        self.session.flush()

        return staff

    def update(
        self,
        staff: Staff,
        *,
        first_name: str,
        last_name: str,
        phone: str,
        position: str,
    ) -> Staff:

        staff.first_name = first_name
        staff.last_name = last_name
        staff.phone = phone
        staff.position = position

        self.session.flush()

        return staff

    def delete(
        self,
        staff: Staff,
    ) -> None:

        self.session.delete(staff)
        self.session.flush()

    def count(
        self,
    ) -> int:


        statement = select(
            func.count(
                Staff.id
            )
        )


        return (
            self.session.scalar(
                statement
            )
            or 0
        )