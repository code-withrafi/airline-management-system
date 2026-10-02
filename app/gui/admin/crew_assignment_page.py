from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
)

from app.gui.components.crew_assignment import (
    CrewAssignmentWidget,
)

from app.services.flight_service import FlightService
from app.services.exceptions import (
    DatabaseOperationError,
)


class CrewAssignmentPage(QWidget):
    """
    Dedicated admin page for managing flight crew assignments.

    A flight is chosen from the combo box at the top; the
    CrewAssignmentWidget below it loads and edits the crew
    for that flight.
    """

    def __init__(
        self,
        session,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.session = session

        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout()

        title = QLabel(
            "Crew Assignment"
        )

        title.setObjectName(
            "pageTitle"
        )

        layout.addWidget(
            title
        )

        picker_row = QHBoxLayout()

        picker_row.addWidget(
            QLabel("Flight:")
        )

        self.flight_selector = QComboBox()

        self.flight_selector.setMinimumWidth(
            280
        )

        self.flight_selector.currentIndexChanged.connect(
            self._on_flight_changed
        )

        picker_row.addWidget(
            self.flight_selector
        )

        picker_row.addStretch()

        layout.addLayout(
            picker_row
        )

        self.crew_widget = CrewAssignmentWidget(
            self.session
        )

        layout.addWidget(
            self.crew_widget
        )

        self.setLayout(
            layout
        )

        self.refresh_flights()

    # ------------------------------------------------------------------
    # Flight list
    # ------------------------------------------------------------------

    def refresh_flights(self):

        current_id = self.flight_selector.currentData()

        self.flight_selector.blockSignals(
            True
        )

        self.flight_selector.clear()

        self.flight_selector.addItem(
            "— Select a flight —",
            None,
        )

        try:

            service = FlightService(
                self.session
            )

            flights = service.get_all_flights()

            for flight in flights:

                label = (
                    f"{flight.flight_number}  "
                    f"({flight.departure_time:%Y-%m-%d %H:%M})"
                )

                self.flight_selector.addItem(
                    label,
                    flight.id,
                )

        except DatabaseOperationError:

            # Leave the combo empty on failure; the widget
            # below will simply show no crew.
            pass

        # Try to restore previous selection
        if current_id is not None:

            index = self.flight_selector.findData(
                current_id
            )

            if index >= 0:

                self.flight_selector.setCurrentIndex(
                    index
                )

        self.flight_selector.blockSignals(
            False
        )

        self._on_flight_changed()

    def _on_flight_changed(self):

        flight_id = self.flight_selector.currentData()

        self.crew_widget.set_flight(
            flight_id
        )
