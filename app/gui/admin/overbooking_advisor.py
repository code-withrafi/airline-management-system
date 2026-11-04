# app/gui/admin/overbooking_advisor.py
"""
Overbooking Advisor panel.

Displays ML-based no-show predictions for the currently-selected
flight. Uses the NoShowService directly (same pattern as other
admin pages — no HTTP needed).
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt


class OverbookingAdvisorPanel(QFrame):
    """
    Panel that shows no-show forecast + safe overbooking recommendation.
    """

    # Palette (matches the rest of the app's blue/gray theme)
    BG           = "#f8fafc"
    BORDER       = "#e2e8f0"
    TITLE_COLOR  = "#0f172a"
    LABEL_COLOR  = "#64748b"
    VALUE_COLOR  = "#0f172a"
    ACCENT       = "#2563eb"
    SUCCESS      = "#16a34a"
    WARNING      = "#b45309"
    DANGER       = "#dc2626"

    def __init__(self, session, parent=None):
        super().__init__(parent)

        self.session = session
        self.current_flight_id = None

        self.setObjectName("OverbookingAdvisorPanel")
        self.setStyleSheet(f"""
            QFrame#OverbookingAdvisorPanel {{
                background-color: {self.BG};
                border: 1px solid {self.BORDER};
                border-radius: 8px;
            }}
            QFrame#OverbookingAdvisorPanel QLabel {{
                border: none;
                background: transparent;
            }}
        """)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(10)

        # --- Header row ---
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("Overbooking Advisor")
        title.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {self.TITLE_COLOR};"
        )
        header.addWidget(title)

        header.addStretch()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.setFixedHeight(26)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        header.addWidget(self.refresh_button)

        outer.addLayout(header)

        # --- Flight label ---
        self.flight_label = QLabel("No flight selected.")
        self.flight_label.setStyleSheet(
            f"color: {self.LABEL_COLOR}; font-size: 12px;"
        )
        outer.addWidget(self.flight_label)

        # --- Metric grid ---
        grid_frame = QWidget()
        grid = QGridLayout(grid_frame)
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(4)

        self.bookings_value = self._metric(grid, 0, 0, "Confirmed bookings")
        self.expected_value = self._metric(grid, 0, 1, "Expected no-shows")
        self.rate_value     = self._metric(grid, 0, 2, "Expected rate")
        self.overbook_value = self._metric(grid, 0, 3, "Safe overbooking")
        self.conf_value     = self._metric(grid, 0, 4, "Confidence")

        outer.addWidget(grid_frame)

        # --- Recommendation banner ---
        self.recommendation = QLabel()
        self.recommendation.setWordWrap(True)
        self.recommendation.setStyleSheet(
            f"color: {self.TITLE_COLOR}; font-size: 12px; padding-top: 4px;"
        )
        outer.addWidget(self.recommendation)

        # --- Error / status line ---
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            f"color: {self.LABEL_COLOR}; font-size: 11px;"
        )
        self.status_label.setVisible(False)
        outer.addWidget(self.status_label)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _metric(self, grid: QGridLayout, row: int, col: int, caption: str) -> QLabel:
        """Add a metric cell (caption + value) at the given grid position."""
        caption_label = QLabel(caption.upper())
        caption_label.setStyleSheet(
            f"color: {self.LABEL_COLOR}; font-size: 10px; "
            f"letter-spacing: 0.5px; font-weight: 600;"
        )
        grid.addWidget(caption_label, row * 2, col)

        value_label = QLabel("—")
        value_label.setStyleSheet(
            f"color: {self.VALUE_COLOR}; font-size: 16px; font-weight: 700;"
        )
        grid.addWidget(value_label, row * 2 + 1, col)

        return value_label

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_for_flight(self, flight_id: int, flight_number: str | None = None) -> None:
        """Load and display forecast for the given flight."""
        self.current_flight_id = flight_id

        if flight_number:
            self.flight_label.setText(f"Flight {flight_number}")
        else:
            self.flight_label.setText(f"Flight ID {flight_id}")

        self._compute_and_render()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _on_refresh_clicked(self) -> None:
        if self.current_flight_id is not None:
            self._compute_and_render()

    def _compute_and_render(self) -> None:
        """Call NoShowService and update the UI."""
        # Try to import the ML service; fail softly if missing.
        try:
            from app.ml.no_show.service import NoShowService
        except Exception as exc:
            self._show_error(
                "ML module not available.",
                detail=str(exc),
            )
            return

        if not NoShowService.is_available():
            self._show_error(
                "No-show model not trained yet.",
                detail="Run: python -m app.ml.no_show.train",
            )
            return

        try:
            service = NoShowService(self.session)
            forecast = service.forecast_flight(self.current_flight_id)
        except Exception as exc:
            self._show_error("Forecast failed.", detail=str(exc))
            return

        # --- Update metrics ---
        bookings = forecast.get("bookings_count", 0)
        expected = forecast.get("expected_no_shows", 0.0)
        rate = forecast.get("expected_no_show_rate", 0.0)
        safe = forecast.get("safe_overbooking", 0)
        conf = forecast.get("confidence", "low")

        self.bookings_value.setText(str(bookings))
        self.expected_value.setText(f"{expected:.2f}")
        self.rate_value.setText(f"{rate * 100:.2f}%")
        self.overbook_value.setText(f"{safe} seat{'s' if safe != 1 else ''}")
        self.conf_value.setText(conf.upper())

        # --- Confidence color ---
        conf_color = {
            "high": self.SUCCESS,
            "medium": self.WARNING,
            "low": self.LABEL_COLOR,
        }.get(conf, self.LABEL_COLOR)
        self.conf_value.setStyleSheet(
            f"color: {conf_color}; font-size: 16px; font-weight: 700;"
        )

        # --- Recommendation banner ---
        recommendation, tone = self._build_recommendation(
            bookings=bookings, expected=expected, safe=safe, conf=conf
        )
        tone_color = {
            "success": self.SUCCESS,
            "warning": self.WARNING,
            "info": self.ACCENT,
            "muted": self.LABEL_COLOR,
        }[tone]
        self.recommendation.setText(recommendation)
        self.recommendation.setStyleSheet(
            f"color: {tone_color}; font-size: 12px; padding-top: 4px;"
        )

        self.status_label.setVisible(False)

    def _build_recommendation(
        self,
        *,
        bookings: int,
        expected: float,
        safe: int,
        conf: str,
    ):
        """Return (message, tone) where tone is one of success/warning/info/muted."""
        if bookings == 0:
            return (
                "ⓘ No active bookings on this flight. Overbooking is not applicable.",
                "muted",
            )

        if conf == "low":
            return (
                f"ⓘ Not enough bookings ({bookings}) for a confident recommendation. "
                f"Consider re-evaluating as more bookings are added.",
                "muted",
            )

        if safe == 0:
            return (
                f"ⓘ Low expected no-shows ({expected:.2f}). "
                f"Do not overbook this flight.",
                "info",
            )

        if safe >= 10:
            return (
                f"✓ Safe to overbook by up to {safe} seat(s). "
                f"Model confidence: {conf.upper()}.",
                "success",
            )

        return (
            f"⚠ Consider overbooking by up to {safe} seat(s). "
            f"Model confidence: {conf.upper()}.",
            "warning",
        )

    def _show_error(self, message: str, detail: str = None) -> None:
        """Show an error state in the panel."""
        self.bookings_value.setText("—")
        self.expected_value.setText("—")
        self.rate_value.setText("—")
        self.overbook_value.setText("—")
        self.conf_value.setText("—")
        self.recommendation.setText(f"⚠ {message}")
        self.recommendation.setStyleSheet(
            f"color: {self.DANGER}; font-size: 12px; padding-top: 4px;"
        )
        if detail:
            self.status_label.setText(detail)
            self.status_label.setVisible(True)
        else:
            self.status_label.setVisible(False)