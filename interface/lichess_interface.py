import sys
import requests
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel,
                               QWidget, QGridLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import serial
import serial.tools.list_ports
import requests
from ConnectWindow import ConnectWindow

def encontrar_porta_esp32():
    portas = serial.tools.list_ports.comports()
    for porta in portas:
        if "USB" in porta.description or "UART" in porta.description or "CP210" in porta.description:
            return porta.device
    return None

# Placeholder for Lichess API token
API_TOKEN = "lip_hXkzeOPTHwXSmjowCchd"
API_HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}"
}

# Define os símbolos ou imagens das peças
PIECES = {
    'P': 'images/white-pawn.png',
    'p': 'images/black-pawn.png',
    'R': 'images/white-rook.png',
    'r': 'images/black-rook.png',
    'N': 'images/white-knight.png',
    'n': 'images/black-knight.png',
    'B': 'images/white-bishop.png',
    'b': 'images/black-bishop.png',
    'Q': 'images/white-queen.png',
    'q': 'images/black-queen.png',
    'K': 'images/white-king.png',
    'k': 'images/black-king.png',
}

# Configuração inicial do tabuleiro em formato FEN simplificado
INITIAL_BOARD = [
    "rnbqkbnr",
    "pppppppp",
    "........",
    "........",
    "........",
    "........",
    "PPPPPPPP",
    "RNBQKBNR",
]

class LichessInterface(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_token = None
        self.setWindowTitle("Lichess Interface")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Add components to the interface
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        self.connect_button = QPushButton("Connect to Lichess")
        self.connect_button.clicked.connect(self.connect_to_lichess)
        self.layout.addWidget(self.connect_button)
        self.new_game_button = QPushButton("New game")
        self.layout.addWidget(self.new_game_button)

        self.board_layout = QGridLayout()
        self.layout.addLayout(self.board_layout)

        self.cells = []
        self.selected_cell = None  # Track the selected cell
        self.initialize_board()

    def initialize_board(self):
        """Creates a simple 8x8 chess board with placeholders."""
        for row, line in enumerate(INITIAL_BOARD):
            row_cells = []
            for col, piece in enumerate(line):
                cell = QLabel()
                cell.setFixedSize(50, 50)
                cell.setAlignment(Qt.AlignCenter)

                # Define a cor da célula
                if (row + col) % 2 == 0:
                    cell.setStyleSheet("background-color: white; border: 1px solid black;")
                else:
                    cell.setStyleSheet("background-color: gray; border: 1px solid black;")

                # Adiciona a peça, se houver
                if piece != '.':
                    pixmap = QPixmap(PIECES[piece])
                    cell.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))


                self.board_layout.addWidget(cell, row, col)
                row_cells.append(cell)
            self.cells.append(row_cells)


    def update_board(self):
        """Atualiza a interface gráfica com base no estado atual do tabuleiro."""
        for row in range(8):
            for col in range(8):
                cell = self.cells[row][col]
                piece = INITIAL_BOARD[row][col]

                # Remove qualquer destaque de seleção
                if (row + col) % 2 == 0:
                    cell.setStyleSheet("background-color: white; border: 1px solid black;")
                else:
                    cell.setStyleSheet("background-color: gray; border: 1px solid black;")

                # Atualiza a peça exibida
                if piece != ".":
                    pixmap = QPixmap(PIECES[piece])
                    cell.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))
                else:
                    cell.clear()

    def connect_to_lichess(self):
        """Connect to Lichess using the API token."""
        self.connect_dialog = ConnectWindow()
        self.connect_dialog.user_data.connect(self.handle_connection)
        self.connect_dialog.show()

    def handle_connection(self, data):
        self.status_label.setText(f"Connected as: {data['user']}")
        self.current_token = data['token']


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = LichessInterface()
    window.show()

    sys.exit(app.exec())