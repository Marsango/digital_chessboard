
import requests

from base_windows.connect_window import Ui_Dialog
from MessageWindow import MessageWindow
from PySide6.QtWidgets import (QDialog)
from PySide6.QtCore import Signal

class ConnectWindow(QDialog, Ui_Dialog):
    user_data = Signal(dict)
    def __init__(self) -> None:
        super(ConnectWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Conectar')
        self.pushButton.clicked.connect(self.connect_to_lichess)
        self.pushButton_2.clicked.connect(self.close)

    def connect_to_lichess(self):
        API_HEADERS = {
            "Authorization": f"Bearer {self.lineEdit.text()}"
        }
        try:
            response = requests.get("https://lichess.org/api/account", headers=API_HEADERS)

            if response.status_code == 200:
                user_data = response.json()
                dialog = MessageWindow('Conectado com sucesso!')
                self.user_data.emit({'user': user_data['username'], 'token': self.lineEdit.text()})
                dialog.exec()
                self.close()
            else:
                dialog = MessageWindow(f'Falha ao conectar: {response.status_code}!')
                dialog.exec()

        except requests.RequestException as e:
            dialog = MessageWindow(f'Erro: {e}')
            dialog.exec()
