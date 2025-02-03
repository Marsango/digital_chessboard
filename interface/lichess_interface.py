import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel,
                               QWidget, QGridLayout, QStackedLayout, QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import serial
import serial.tools.list_ports
import json
import threading
import requests
from ConnectWindow import ConnectWindow


def encontrar_porta_esp32():
    portas = serial.tools.list_ports.comports()
    for porta in portas:
        if "USB" in porta.description or "UART" in porta.description or "CP210" in porta.description:
            return porta.device
    return None


thread_running = True








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
        self.setGeometry(100, 100, 460, 542)
        self.setMaximumWidth(460)
        self.setMaximumHeight(542)
        self.setWindowIcon(QPixmap('images/black-knight.png'))
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        self.misc_layout = QStackedLayout()
        self.layout.addLayout(self.misc_layout)
        self.central_widget.setLayout(self.layout)
        self.connect_layout = self.create_connect_layout()
        self.connected_layout = self.create_connected_layout()
        self.in_game_layout = self.create_in_game_layout()

        self.misc_layout.addWidget(self.connect_layout)
        self.misc_layout.addWidget(self.connected_layout)
        self.misc_layout.addWidget(self.in_game_layout)
        self.switch_layout(0)
        # Add components to the interface

        self.board_layout = QGridLayout()
        self.layout.addLayout(self.board_layout)

        self.cells = []
        self.selected_cell = None  # Track the selected cell
        self.initialize_board()

    def create_connected_layout(self):
        widget = QWidget()
        self.new_game_button = QPushButton("New game")
        self.new_game_button.clicked.connect(self.new_game_lichess)
        layout = QVBoxLayout(widget)
        layout.addWidget(self.new_game_button)
        return widget

    def create_connect_layout(self):
        widget = QWidget()
        self.connect_button = QPushButton("Connect to Lichess")
        self.connect_button.clicked.connect(self.connect_to_lichess)
        layout = QVBoxLayout(widget)
        layout.addWidget(self.connect_button)
        return widget

    def create_in_game_layout(self):
        widget = QWidget()
        self.resign_button = QPushButton("Resign")
        self.opponent = QLabel("zezinho (1300)")
        self.last_move = QLabel("e4")
        self.your_time = QLabel("1:00")
        self.opponent_time = QLabel("1:00")
        layout = QHBoxLayout(widget)
        layout.addWidget(self.resign_button)
        layout.addWidget(self.opponent)
        layout.addWidget(self.last_move)
        layout.addWidget(self.your_time)
        layout.addWidget(self.opponent_time)
        return widget

    def switch_layout(self, index):
        self.misc_layout.setCurrentIndex(index)

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

    def stream_lichess_events(self):
        global thread_running
        url = "https://lichess.org/api/stream/event"
        headers = {"Authorization": f"Bearer {self.current_token}"}

        with requests.get(url, headers=headers, stream=True) as response:
            for line in response.iter_lines():
                if not thread_running:
                    print("Encerrando a thread...")
                    break
                if line:
                    event = json.loads(line)
                    print(f"Evento recebido: {event}")
                    self.handle_event(event)

    def handle_event(self, event):
        if event['type'] == 'gameStart':
            self.switch_layout(2)
            self.opponent.setText(f"{event['game']['opponent']['username']} ({event['game']['opponent']['rating']})" )
        elif event['type'] == 'gameFinish':
            self.switch_layout(1)

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
        global thread_running
        self.current_token = data['token']
        if data['token'] is not None:
            self.status_label.setText(f"Connected as: {data['user']}")
            self.switch_layout(1)
            thread_running = True
            thread = threading.Thread(target=self.stream_lichess_events, daemon=True)
            thread.start()
        else:
            self.status_label.setText(f"Status: failed to connected")
            thread_running = False

    def new_game_lichess(self):
        if self.current_token:
            ...


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = LichessInterface()
    window.show()

    sys.exit(app.exec())
