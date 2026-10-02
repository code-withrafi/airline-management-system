APP_STYLE = """
QWidget {
    font-family: "Segoe UI";
    font-size: 14px;
    color: #1f2937;
}

QMainWindow {
    background-color: #f5f7fb;
}

QFrame#loginCard {
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
}

QLabel#titleLabel {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
}

QLabel#subtitleLabel {
    font-size: 14px;
    color: #6b7280;
}

QLabel#fieldLabel {
    font-size: 13px;
    font-weight: 600;
    color: #374151;
}

QLineEdit {
    min-height: 44px;
    padding: 0 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    background-color: #ffffff;
    color: #111827;
}

QLineEdit:focus {
    border: 2px solid #2563eb;
}

QPushButton#loginButton {
    min-height: 46px;
    border: none;
    border-radius: 8px;
    background-color: #2563eb;
    color: white;
    font-size: 15px;
    font-weight: 600;
}

QPushButton#loginButton:hover {
    background-color: #1d4ed8;
}

QPushButton#loginButton:pressed {
    background-color: #1e40af;
}

QPushButton#loginButton:disabled {
    background-color: #93c5fd;
}

QLabel#errorLabel {
    color: #dc2626;
    font-size: 13px;
}

QLabel#footerLabel {
    color: #9ca3af;
    font-size: 12px;
}
"""