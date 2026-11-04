# app/gui/admin/schedule_generator.py
"""
Admin page for bulk flight schedule generation.

Runs the FlightScheduleGenerator on a background thread so the UI
stays responsive. Shows live progress, a log stream, and a summary
when complete.
"""

from datetime import date, timedelta

from PySide6.QtCore import (
    QDate,
    QObject,
    Qt,
    QThread,
    Signal,
)

from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config.database import SessionLocal
from app.models.aircraft import Aircraft, AircraftStatus
from app.models.route import Route
from app.services.schedule.service import (
    FlightScheduleGenerator,
    ScheduleGenerationError,
)


# ======================================================================
# Background worker
# ======================================================================

class _GenerationWorker(QObject):
    """Runs FlightScheduleGenerator in a worker thread."""

    progress = Signal(int, int, str)       # current, total, message
    log = Signal(str)
    finished = Signal(dict)                # summary dict
    error = Signal(str)

    def __init__(self, start_date, end_date, overwrite_existing):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        self.overwrite_existing = overwrite_existing

    def run(self):
        session = SessionLocal()
        try:
            self.log.emit(f"Generating flights from {self.start_date} to {self.end_date}...")

            generator = FlightScheduleGenerator(session)

            def on_progress(current, total, message):
                self.progress.emit(current, total, message)

            result = generator.generate(
                start_date=self.start_date,
                end_date=self.end_date,
                overwrite_existing=self.overwrite_existing,
                on_progress=on_progress,
            )

            self.log.emit(
                f"Done. Created={result['created']} "
                f"Skipped={result['skipped_no_aircraft']} "
                f"Duration={result['duration_seconds']}s"
            )
            self.finished.emit(result)

        except ScheduleGenerationError as exc:
            self.error.emit(str(exc))
        except Exception as exc:
            import traceback
            self.error.emit(f"Unexpected error: {exc}\n\n{traceback.format_exc()}")
        finally:
            session.close()


# ======================================================================
# Main page
# ======================================================================

class ScheduleGeneratorPage(QWidget):
    """Admin page for bulk flight schedule generation."""

    # Signal so admin_window can refresh other pages after generation
    generation_completed = Signal()

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session

        self._thread = None
        self._worker = None

        self._build_ui()
        self._refresh_fleet_stats()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 28)
        outer.setSpacing(18)

        # Title block
        title = QLabel("Flight Schedule Generator")
        title.setObjectName("scheduleTitle")
        outer.addWidget(title)

        subtitle = QLabel(
            "Bulk-generate flights across all active routes. Aircraft are "
            "assigned with round-trip rules, fares are computed dynamically, "
            "and existing flights can be safely overwritten."
        )
        subtitle.setObjectName("scheduleSubtitle")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        # Two-column layout
        columns = QHBoxLayout()
        columns.setSpacing(20)

        # ---------------- LEFT: parameters ----------------
        left = QFrame()
        left.setObjectName("scheduleCard")
        left.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(22, 22, 22, 22)
        left_layout.setSpacing(14)

        left_title = QLabel("Schedule Parameters")
        left_title.setObjectName("cardTitle")
        left_layout.addWidget(left_title)

        # Start date
        left_layout.addWidget(self._make_label("Start date"))
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDisplayFormat("yyyy-MM-dd")
        self.start_date_input.setDate(QDate.currentDate())
        self.start_date_input.setMinimumHeight(38)
        self.start_date_input.setObjectName("scheduleDateEdit")
        left_layout.addWidget(self.start_date_input)

        # End date
        left_layout.addWidget(self._make_label("End date"))
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDisplayFormat("yyyy-MM-dd")
        self.end_date_input.setDate(QDate.currentDate().addMonths(1))
        self.end_date_input.setMinimumHeight(38)
        self.end_date_input.setObjectName("scheduleDateEdit")
        left_layout.addWidget(self.end_date_input)

        # Presets
        left_layout.addWidget(self._make_label("Quick presets"))
        preset_row = QHBoxLayout()
        preset_row.setSpacing(6)

        for label, months in [
            ("1 month", 1),
            ("3 months", 3),
            ("6 months", 6),
            ("1 year", 12),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("schedulePreset")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, m=months: self._apply_preset(m)
            )
            preset_row.addWidget(btn)

        left_layout.addLayout(preset_row)

        # Options
        left_layout.addWidget(self._make_label("Options"))
        self.overwrite_checkbox = QCheckBox("Overwrite existing flights in range")
        self.overwrite_checkbox.setObjectName("scheduleCheckbox")
        self.overwrite_checkbox.setChecked(False)
        left_layout.addWidget(self.overwrite_checkbox)

        warn = QLabel(
            "⚠ Overwriting will delete SCHEDULED flights in the range. "
            "Flights with active bookings are always preserved."
        )
        warn.setObjectName("scheduleWarning")
        warn.setWordWrap(True)
        left_layout.addWidget(warn)

        # Info block
        left_layout.addSpacing(8)
        left_layout.addWidget(self._make_label("Fleet status"))
        self.fleet_info = QLabel()
        self.fleet_info.setObjectName("scheduleInfo")
        self.fleet_info.setWordWrap(True)
        left_layout.addWidget(self.fleet_info)

        left_layout.addWidget(self._make_label("Generation rules"))
        rules = QLabel(
            "• Domestic routes: 3 flights per day\n"
            "• International: 1 per day (2 on weekends)\n"
            "• Aircraft turnaround: 45m domestic / 90m international\n"
            "• Fares: dynamically computed per flight"
        )
        rules.setObjectName("scheduleInfo")
        rules.setWordWrap(True)
        left_layout.addWidget(rules)

        left_layout.addStretch()

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.refresh_stats_button = QPushButton("Refresh Stats")
        self.refresh_stats_button.setObjectName("scheduleSecondary")
        self.refresh_stats_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_stats_button.setMinimumHeight(42)
        self.refresh_stats_button.clicked.connect(self._refresh_fleet_stats)
        actions.addWidget(self.refresh_stats_button)

        self.generate_button = QPushButton("Generate Flights")
        self.generate_button.setObjectName("schedulePrimary")
        self.generate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_button.setMinimumHeight(42)
        self.generate_button.clicked.connect(self._on_generate_clicked)
        actions.addWidget(self.generate_button, 1)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("scheduleDanger")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setMinimumHeight(42)
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        actions.addWidget(self.cancel_button)

        left_layout.addLayout(actions)

        columns.addWidget(left, 1)

        # ---------------- RIGHT: progress ----------------
        right = QFrame()
        right.setObjectName("scheduleCard")
        right.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(22, 22, 22, 22)
        right_layout.setSpacing(14)

        right_title = QLabel("Generation Status")
        right_title.setObjectName("cardTitle")
        right_layout.addWidget(right_title)

        # Status text
        self.status_label = QLabel("Idle — ready to generate.")
        self.status_label.setObjectName("scheduleStatus")
        right_layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("scheduleProgress")
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(22)
        right_layout.addWidget(self.progress_bar)

        # Summary grid
        summary_row = QHBoxLayout()
        summary_row.setSpacing(20)

        self.created_value = self._make_stat(summary_row, "Created", "—")
        self.skipped_value = self._make_stat(summary_row, "Skipped", "—")
        self.duration_value = self._make_stat(summary_row, "Duration", "—")
        self.deleted_value = self._make_stat(summary_row, "Deleted", "—")

        right_layout.addLayout(summary_row)

        right_layout.addWidget(self._make_label("Log"))

        self.log_view = QTextEdit()
        self.log_view.setObjectName("scheduleLog")
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(220)
        self.log_view.setPlaceholderText("Generation log will appear here...")
        right_layout.addWidget(self.log_view, 1)

        columns.addWidget(right, 1)

        outer.addLayout(columns, 1)

    def _make_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("scheduleFieldLabel")
        return label

    def _make_stat(self, layout, caption: str, initial: str) -> QLabel:
        """Add a stat tile to the layout; return its value QLabel."""
        container = QWidget()
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)

        caption_label = QLabel(caption.upper())
        caption_label.setObjectName("scheduleStatCaption")

        value_label = QLabel(initial)
        value_label.setObjectName("scheduleStatValue")

        v.addWidget(caption_label)
        v.addWidget(value_label)

        layout.addWidget(container)
        return value_label

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------

    def _apply_preset(self, months: int):
        """Set the end date to start_date + N months."""
        start_qd = self.start_date_input.date()
        start_date = date(start_qd.year(), start_qd.month(), start_qd.day())

        # Approximate month arithmetic by using days = months * 30
        end_date = start_date + timedelta(days=months * 30)
        self.end_date_input.setDate(QDate(end_date.year, end_date.month, end_date.day))

    # ------------------------------------------------------------------
    # Fleet stats
    # ------------------------------------------------------------------

    def _refresh_fleet_stats(self):
        try:
            n_aircraft = (
                self.session.query(Aircraft)
                .filter(Aircraft.status == AircraftStatus.ACTIVE)
                .count()
            )
            n_routes = (
                self.session.query(Route)
                .filter(Route.is_active == True)  # noqa: E712
                .count()
            )
            self.fleet_info.setText(
                f"• {n_aircraft} active aircraft\n"
                f"• {n_routes} active routes"
            )
        except Exception as exc:
            self.fleet_info.setText(f"Unable to load stats: {exc}")

    # ------------------------------------------------------------------
    # Generate flow
    # ------------------------------------------------------------------

    def _on_generate_clicked(self):
        if self._thread is not None and self._thread.isRunning():
            QMessageBox.information(self, "Busy", "A generation is already running.")
            return

        # Validate dates
        start_qd = self.start_date_input.date()
        end_qd = self.end_date_input.date()

        start_date = date(start_qd.year(), start_qd.month(), start_qd.day())
        end_date = date(end_qd.year(), end_qd.month(), end_qd.day())

        if end_date < start_date:
            QMessageBox.warning(self, "Invalid Range", "End date must be on or after start date.")
            return

        days = (end_date - start_date).days + 1

        # Confirm
        msg = (
            f"Generate flights from {start_date} to {end_date}\n"
            f"({days} day{'s' if days != 1 else ''})\n\n"
        )
        if self.overwrite_checkbox.isChecked():
            msg += "⚠ OVERWRITE MODE: scheduled flights in this range will be DELETED.\n"
            msg += "Flights with active bookings are preserved.\n\n"
        msg += "Continue?"

        confirm = QMessageBox.question(
            self,
            "Confirm Generation",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        # Reset UI
        self.progress_bar.setValue(0)
        self.log_view.clear()
        self.created_value.setText("—")
        self.skipped_value.setText("—")
        self.duration_value.setText("—")
        self.deleted_value.setText("—")
        self.status_label.setText("Starting...")

        # Disable inputs during run
        self._set_inputs_enabled(False)
        self.generate_button.setEnabled(False)
        self.cancel_button.setVisible(True)

        # Start worker
        self._thread = QThread()
        self._worker = _GenerationWorker(
            start_date=start_date,
            end_date=end_date,
            overwrite_existing=self.overwrite_checkbox.isChecked(),
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._append_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)

        self._thread.start()

    def _on_cancel_clicked(self):
        if self._thread is None or not self._thread.isRunning():
            return
        # Request interruption; the worker will stop after current batch
        self._thread.requestInterruption()
        self._append_log("⚠ Cancellation requested — will stop after current batch.")

    # ------------------------------------------------------------------
    # Worker callbacks
    # ------------------------------------------------------------------

    def _on_progress(self, current: int, total: int, message: str):
        if total <= 0:
            return
        pct = int((current / total) * 100)
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"{pct}% — {message}")

    def _append_log(self, line: str):
        self.log_view.append(line)

    def _on_finished(self, result: dict):
        # Close thread
        self._thread.quit()
        self._thread.wait()
        self._thread = None
        self._worker = None

        # Update UI
        self.progress_bar.setValue(100)
        self.status_label.setText("✓ Generation complete.")
        self.created_value.setText(str(result["created"]))
        self.skipped_value.setText(str(result["skipped_no_aircraft"]))
        self.duration_value.setText(f"{result['duration_seconds']}s")
        self.deleted_value.setText(str(result["deleted_existing"]))

        # Summary log
        self._append_log("─" * 40)
        self._append_log(f"Created:  {result['created']}")
        self._append_log(f"Deleted:  {result['deleted_existing']}")
        self._append_log(f"Skipped (no aircraft): {result['skipped_no_aircraft']}")
        self._append_log(f"Skipped (duplicate):   {result['skipped_duplicate']}")
        if result["errors"]:
            self._append_log(f"Errors:   {len(result['errors'])}")
            for e in result["errors"][:5]:
                self._append_log(f"  • {e}")

        # Re-enable
        self._set_inputs_enabled(True)
        self.generate_button.setEnabled(True)
        self.cancel_button.setVisible(False)

        # Notify parent (so it can refresh flights page)
        self.generation_completed.emit()

        QMessageBox.information(
            self,
            "Generation Complete",
            f"Created {result['created']} flight(s).\n"
            f"Skipped {result['skipped_no_aircraft']} (no aircraft).\n"
            f"Duration: {result['duration_seconds']}s",
        )

    def _on_error(self, message: str):
        # Close thread
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None

        self.status_label.setText("✗ Error occurred.")
        self._append_log(f"ERROR: {message}")

        self._set_inputs_enabled(True)
        self.generate_button.setEnabled(True)
        self.cancel_button.setVisible(False)

        QMessageBox.critical(self, "Generation Failed", message)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_inputs_enabled(self, enabled: bool):
        self.start_date_input.setEnabled(enabled)
        self.end_date_input.setEnabled(enabled)
        self.overwrite_checkbox.setEnabled(enabled)