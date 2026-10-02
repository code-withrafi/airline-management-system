from PySide6.QtWidgets import (
    QWidget,
    QComboBox,
    QVBoxLayout,
    QLabel,
)

from sqlalchemy.orm import Session


from app.services.flight_assignment_service import (
    FlightAssignmentService,
)



class AircraftSelector(QWidget):
    """
    Reusable aircraft dropdown component.
    Loads only available aircraft.
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


        self.service = (
            FlightAssignmentService(
                session
            )
        )


        self.aircraft_map = {}


        self.setup_ui()


        self.load_aircraft()



    def setup_ui(self):

        layout = QVBoxLayout()


        self.label = QLabel(
            "Aircraft:"
        )


        self.combo_box = QComboBox()


        layout.addWidget(
            self.label
        )


        layout.addWidget(
            self.combo_box
        )


        self.setLayout(
            layout
        )



    def load_aircraft(self):

        self.combo_box.clear()

        self.aircraft_map.clear()


        aircraft_list = (
            self.service
            .get_available_aircraft()
        )


        if not aircraft_list:

            self.combo_box.addItem(
                "No aircraft available"
            )

            self.combo_box.setEnabled(
                False
            )

            return



        for aircraft in aircraft_list:


            display_text = (
                f"{aircraft.registration_number}"
                f" - "
                f"{aircraft.manufacturer}"
                f" "
                f"{aircraft.model}"
            )


            self.combo_box.addItem(
                display_text
            )


            index = (
                self.combo_box
                .count()
                -
                1
            )


            self.aircraft_map[index] = (
                aircraft.id
            )



    def get_selected_aircraft_id(
        self,
    ) -> int | None:


        index = (
            self.combo_box
            .currentIndex()
        )


        return (
            self.aircraft_map
            .get(index)
        )



    def refresh(self):

        self.load_aircraft()