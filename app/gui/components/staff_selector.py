from PySide6.QtWidgets import (
    QComboBox,
)

from sqlalchemy.orm import Session

from app.repositories import StaffRepository



class StaffSelector(QComboBox):
    """
    Reusable dropdown component for selecting staff.
    """


    def __init__(
        self,
        session: Session,
        parent=None,
    ):

        super().__init__(
            parent
        )


        self.session = session


        self.repository = (
            StaffRepository(
                session
            )
        )


        self.staff_map = {}


        self.setMinimumWidth(
            250
        )


        self.load_staff()



    def load_staff(self):

        """
        Loads staff from database.
        """


        self.clear()


        self.staff_map.clear()


        staff_list = (
            self.repository
            .get_all()
        )


        for staff in staff_list:


            display_text = (
                f"{staff.employee_id}"
                " - "
                f"{staff.first_name}"
                " "
                f"{staff.last_name}"
            )


            self.addItem(
                display_text
            )


            self.staff_map[
                self.count() - 1
            ] = staff.id



    def get_selected_staff_id(
        self,
    ) -> int | None:

        """
        Returns selected staff database ID.
        """


        index = (
            self.currentIndex()
        )


        if index < 0:

            return None


        return self.staff_map.get(
            index
        )



    def refresh(
        self,
    ):

        """
        Reload staff list.
        """

        self.load_staff()