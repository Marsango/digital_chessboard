from base_windows.message_window import Ui_Dialog
from PySide6.QtWidgets import (QDialog)

class MessageWindow(QDialog, Ui_Dialog):
    def __init__(self, message) -> None:
        super(MessageWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Conectar')
        self.message.setText(message)
        self.Ok.clicked.connect(self.close)

