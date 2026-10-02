from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)


class DashboardCard(QFrame):
    """
    Reusable dashboard statistics card.

    The component is intentionally independent from the database
    and service layers. It only displays data supplied by the GUI.
    """

    def __init__(
        self,
        title: str,
        value: int | str = 0,
        icon: str = "",
        subtitle: str = "",
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName("dashboardCard")
        self.setMinimumHeight(130)
        self.setMaximumHeight(150)

        self._build_ui(
            title=title,
            value=value,
            icon=icon,
            subtitle=subtitle,
        )

    def _build_ui(
        self,
        title: str,
        value: int | str,
        icon: str,
        subtitle: str,
    ) -> None:
        """Build the card interface."""

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        main_layout.setSpacing(16)

        # --------------------------------------------------------------
        # Icon
        # --------------------------------------------------------------

        self.icon_label = QLabel(icon)

        self.icon_label.setObjectName(
            "dashboardCardIcon"
        )

        self.icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.icon_label.setMinimumSize(
            52,
            52,
        )

        self.icon_label.setMaximumSize(
            52,
            52,
        )

        # --------------------------------------------------------------
        # Text area
        # --------------------------------------------------------------

        text_layout = QVBoxLayout()

        text_layout.setSpacing(4)

        text_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.title_label = QLabel(title)

        self.title_label.setObjectName(
            "dashboardCardTitle"
        )

        self.title_label.setWordWrap(True)

        self.value_label = QLabel(str(value))

        self.value_label.setObjectName(
            "dashboardCardValue"
        )

        self.subtitle_label = QLabel(subtitle)

        self.subtitle_label.setObjectName(
            "dashboardCardSubtitle"
        )

        self.subtitle_label.setWordWrap(True)

        text_layout.addWidget(
            self.title_label
        )

        text_layout.addWidget(
            self.value_label
        )

        if subtitle:
            text_layout.addWidget(
                self.subtitle_label
            )

        text_layout.addStretch()

        # --------------------------------------------------------------
        # Main layout
        # --------------------------------------------------------------

        main_layout.addWidget(
            self.icon_label
        )

        main_layout.addLayout(
            text_layout,
            1,
        )

        # --------------------------------------------------------------
        # Component stylesheet
        # --------------------------------------------------------------

        self.setStyleSheet(
            """
            QFrame#dashboardCard {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
            }

            QFrame#dashboardCard:hover {
                border: 1px solid #CBD5E1;
            }

            QLabel#dashboardCardIcon {
                background-color: #F1F5F9;
                border-radius: 12px;
                color: #1E293B;
                font-size: 24px;
                font-weight: 600;
            }

            QLabel#dashboardCardTitle {
                color: #64748B;
                font-size: 13px;
                font-weight: 500;
            }

            QLabel#dashboardCardValue {
                color: #0F172A;
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#dashboardCardSubtitle {
                color: #94A3B8;
                font-size: 11px;
                font-weight: 400;
            }
            """
        )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def set_value(self, value: int | str) -> None:
        """Update the displayed statistic value."""

        self.value_label.setText(
            str(value)
        )

    def set_title(self, title: str) -> None:
        """Update the card title."""

        self.title_label.setText(
            title
        )

    def set_subtitle(self, subtitle: str) -> None:
        """Update the card subtitle."""

        self.subtitle_label.setText(
            subtitle
        )

    def set_icon(self, icon: str) -> None:
        """Update the card icon."""

        self.icon_label.setText(
            icon
        )