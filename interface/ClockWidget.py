from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ClockWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel("00:00", self)
        self.label.setFont(QFont("Arial", 20, QFont.Bold))
        self.label.setStyleSheet(
            "color: white; "
            "background-color: black; "
            "border-radius: 15px; "
            "padding: 10px; "
            "border: 2px solid white;"
        )
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMaximumWidth(90)
        self.label.setMaximumHeight(50)
        self.label.setMinimumWidth(90)
        self.label.setMinimumHeight(50)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def setText(self, text):
        self.label.setText(text)

    def text(self):
        return self.label.text()