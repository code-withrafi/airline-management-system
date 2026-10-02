from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)


class PdfPreviewDialog(QDialog):
    """
    After generating a PDF to a temporary location, ask the user
    where to save it (or just open it).
    """

    def __init__(
        self,
        parent,
        temp_path,
        suggested_name,
        title="PDF Ready",
    ):

        super().__init__(parent)

        self.temp_path = Path(temp_path)
        self.suggested_name = suggested_name

        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        info = QLabel(
            "Your document was generated.\n\n"
            "You can save it to a location of your choice or "
            "open it now with your default viewer."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        buttons = QDialogButtonBox()
        save_button = buttons.addButton(
            "Save As...",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        open_button = buttons.addButton(
            "Open",
            QDialogButtonBox.ButtonRole.ActionRole,
        )
        close_button = buttons.addButton(
            "Close",
            QDialogButtonBox.ButtonRole.RejectRole,
        )

        save_button.clicked.connect(self._save_as)
        open_button.clicked.connect(self._open)
        close_button.clicked.connect(self.reject)

        layout.addWidget(buttons)

    def _save_as(self):

        target, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF",
            self.suggested_name,
            "PDF files (*.pdf)",
        )

        if not target:
            return

        try:
            data = self.temp_path.read_bytes()
            Path(target).write_bytes(data)
            QMessageBox.information(
                self,
                "Saved",
                f"Saved to:\n{target}",
            )
            self.accept()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Save Failed",
                str(error),
            )

    def _open(self):

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(self.temp_path))
        )