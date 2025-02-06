import sys
import time

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel,
                               QWidget, QGridLayout, QStackedLayout, QHBoxLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
import serial
import serial.tools.list_ports
import json
import threading
import requests
import copy
from ConnectWindow import ConnectWindow
from SearchAGame import SearchAGame


def encontrar_porta_esp32():
    portas = serial.tools.list_ports.comports()
    for porta in portas:
        if "USB" in porta.description or "UART" in porta.description or "CP210" in porta.description:
            return porta.device
    return None


queue_thread = True
game_thread = True

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
INITIAL_BOARD = [['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
['.', '.', '.', '.', '.', '.', '.', '.'],
['.', '.', '.', '.', '.', '.', '.', '.'],
['.', '.', '.', '.', '.', '.', '.', '.'],
['.', '.', '.', '.', '.', '.', '.', '.'],
['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']]
CURRENT_BOARD = copy.deepcopy(INITIAL_BOARD)
from PySide6.QtCore import Signal


class LichessInterface(QMainWindow):
    start_timer_signal = Signal()
    def __init__(self):
        super().__init__()

        self.to_move = 'white'
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
        self.current_color = 'white'
        self.update_board()
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.update_time)
        self.start_timer_signal.connect(self.start_timer_main_thread)

    def create_connected_layout(self):
        widget = QWidget()
        self.result_label = QLabel("Result: --")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.new_game_button = QPushButton("New game")
        self.new_game_button.clicked.connect(self.new_game_lichess)
        layout = QVBoxLayout(widget)
        layout.addWidget(self.result_label)
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
        self.opponent = QLabel("Unknown (00)")
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
        for row, line in enumerate(CURRENT_BOARD):
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
        global queue_thread
        url = "https://lichess.org/api/stream/event"
        headers = {"Authorization": f"Bearer {self.current_token}"}

        with requests.get(url, headers=headers, stream=True) as response:
            for line in response.iter_lines():
                if not queue_thread:
                    print("Encerrando a thread...")
                    break
                if line:
                    event = json.loads(line)
                    print(f"Evento recebido: {event}")
                    self.handle_event(event)

    def stream_game(self):
        global game_thread
        url = f"https://lichess.org/api/board/game/stream/{self.current_game}"
        headers = {"Authorization": f"Bearer {self.current_token}"}

        with requests.get(url, headers=headers, stream=True) as response:
            for line in response.iter_lines():
                if not game_thread:
                    print("Encerrando a thread...")
                    break
                if line:
                    event = json.loads(line)
                    print(f"Evento recebido: {event}")
                    self.handle_game_events(event)

    def letter_position(self, letter):
        return ord(letter.lower()) - ord('a')

    def translate_move(self, move):
        if len(move) == 5:
            return f'{move[2]}{move[3]}={move[4]}'
        else:
            square_to_erase = move[0] + move[1]
            square_to_fill = move[2] + move[3]
            if (square_to_erase == 'e1' and square_to_fill == 'g1' and CURRENT_BOARD[7][4].upper()) == 'K' or ( square_to_erase == 'e8' and square_to_fill == 'g8' and CURRENT_BOARD[0][4] == 'k'):
                return 'O-O'
            elif (square_to_erase == 'e1' and square_to_fill == 'c1' and CURRENT_BOARD[7][4].upper() == 'K') or (square_to_erase == 'e8' and square_to_fill == 'c8' and CURRENT_BOARD[0][4] == 'k'):
                return 'O-O-O'
            elif CURRENT_BOARD[8 - int(move[1])][self.letter_position(move[0])].lower() != 'p':
                if CURRENT_BOARD[8 - int(move[3])][self.letter_position(move[2])].lower() != '.':
                    return f'{CURRENT_BOARD[8 - int(move[1])][self.letter_position(move[0])].upper()}x{move[2]}{move[3]}'
                else:
                    return f'{CURRENT_BOARD[8 - int(move[1])][self.letter_position(move[0])].upper()}{move[2]}{move[3]}'
            else:
                if CURRENT_BOARD[8 - int(move[3])][self.letter_position(move[2])].lower() != '.':
                    return f'{move[0]}x{move[2]}{move[3]}'
                else:
                    return f'{move[2]}{move[3]}'

    def handle_game_events(self, event):
        try:
            if event['type'] == 'gameState' and event['status'] != 'aborted':
                self.move_timer.stop()
                last_move = event['moves'].split()[-1]
                white_time = event['wtime'] / 1000
                black_time = event['btime'] / 1000
                if len(event['moves'].split(' ')) % 2 == 0:
                    self.to_move = 'white'
                else:
                    self.to_move = 'black'
                self.your_time.setText(f'{int(white_time / 60)}:{int(white_time % 60):02d}')
                self.opponent_time.setText(f'{int(black_time / 60)}:{int(black_time % 60):02d}')
                self.last_move.setText(f'Last move: {self.translate_move(last_move)}')
                self.make_ui_move(last_move)
                self.update_board()
                if len(event['moves'].split(' ')) >= 2:
                    self.start_timer_signal.emit()  # Emite o sinal para iniciar o timer
        except:
            print(f"ERROR: {event}")

    def start_timer_main_thread(self):
        self.move_timer.start(1000)

    def update_time(self):
        print('reached')
        if game_thread is False:
            self.move_timer.stop()
        elif self.to_move == 'white':
            current_time_minutes = int(self.your_time.text().split(':')[0])
            current_time_seconds = int(self.your_time.text().split(':')[1])
            new_time = (current_time_minutes * 60 + current_time_seconds - 1)
            self.your_time.setText(f'{int(new_time / 60)}:{int(new_time % 60):02d}')
        else:
            current_time_minutes = int(self.opponent_time.text().split(':')[0])
            current_time_seconds = int(self.opponent_time.text().split(':')[1])
            new_time = (current_time_minutes * 60 + current_time_seconds - 1)
            self.opponent_time.setText(f'{int(new_time / 60)}:{int(new_time % 60):02d}')

    def make_ui_move(self, move):
        square_to_erase = move[0] + move[1]
        square_to_fill = move[2] + move[3]
        if square_to_erase == 'e1' and square_to_fill == 'g1' and CURRENT_BOARD[7][4].upper() == 'K':
            CURRENT_BOARD[7][6] = 'K'
            CURRENT_BOARD[7][5] = 'R'
            CURRENT_BOARD[7][4] = '.'
            CURRENT_BOARD[7][7] = '.'
        elif square_to_erase == 'e1' and square_to_fill == 'c1' and CURRENT_BOARD[7][4].upper() == 'K':
            CURRENT_BOARD[7][2] = 'K'
            CURRENT_BOARD[7][3] = 'R'
            CURRENT_BOARD[7][4] = '.'
            CURRENT_BOARD[7][0] = '.'
        elif square_to_erase == 'e8' and square_to_fill == 'g8' and CURRENT_BOARD[0][4] == 'k':
            CURRENT_BOARD[0][6] = 'k'
            CURRENT_BOARD[0][5] = 'r'
            CURRENT_BOARD[0][4] = '.'
            CURRENT_BOARD[0][7] = '.'
        elif square_to_erase == 'e8' and square_to_fill == 'c8' and CURRENT_BOARD[0][4] == 'k':
            CURRENT_BOARD[0][2] = 'k'
            CURRENT_BOARD[0][3] = 'r'
            CURRENT_BOARD[0][4] = '.'
            CURRENT_BOARD[0][0] = '.'
        elif square_to_erase[1] == '7' and CURRENT_BOARD[8 - int(square_to_erase[1])][self.letter_position(square_to_erase[0])] == 'P':
            CURRENT_BOARD[8 - int(square_to_erase[1])][self.letter_position(square_to_erase[0])] = '.'
            CURRENT_BOARD[8 - int(square_to_fill[1])][self.letter_position(square_to_fill[0])] = move[-1].upper()
        elif square_to_erase[1] == '2' and CURRENT_BOARD[8 - int(square_to_erase[1])][self.letter_position(square_to_erase[0])] == 'p':
            CURRENT_BOARD[8 - int(square_to_erase[1])][self.letter_position(square_to_erase[0])] = '.'
            CURRENT_BOARD[8 - int(square_to_fill[1])][self.letter_position(square_to_fill[0])] = move[-1].lower()
        else:
            CURRENT_BOARD[8 - int(square_to_fill[1])][self.letter_position(square_to_fill[0])] = CURRENT_BOARD[8 - int(square_to_erase[1])][self.letter_position(square_to_erase[0])]
            CURRENT_BOARD[8 - int(square_to_erase[1])][self.letter_position(square_to_erase[0])] = '.'

    def handle_event(self, event):
        global game_thread
        global CURRENT_BOARD
        if event['type'] == 'gameStart':
            self.switch_layout(2)
            if event['game']['source'] != 'ai':
                self.opponent.setText(
                    f"{event['game']['opponent']['username']} ({event['game']['opponent']['rating']})")
            else:
                self.opponent.setText(f"{event['game']['opponent']['username']}")
            self.current_game = event['game']['gameId']
            self.current_color = event['game']["color"]
            self.last_move.setText('Last move: --')
            self.your_time.setText('-:--')
            self.opponent_time.setText('-:--')
            CURRENT_BOARD = copy.deepcopy(INITIAL_BOARD)
            self.update_board()
            game_thread = True
            thread = threading.Thread(target=self.stream_game, daemon=True)
            thread.start()
        elif event['type'] == 'gameFinish':
            self.switch_layout(1)
            if event['game']['status']['name'] != 'aborted':
                if not 'winner' in event['game']:
                    self.result_label.setText('1/2-1/2')
                elif event['game']['winner'] == 'black':
                    self.result_label.setText('0-1')
                elif event['game']['winner'] == 'white':
                    self.result_label.setText('1-0')
                else:
                    self.result_label.setText('1/2-1/2')
            else:
                self.result_label.setText('Aborted')
            self.current_game = None
            game_thread = False

    def update_board(self):
        """Atualiza a interface gráfica com base no estado atual do tabuleiro."""
        for row in range(8):
            for col in range(8):
                if self.current_color == 'black':
                    cell = self.cells[7 - row][7 - col]
                else:
                    cell = self.cells[row][col]
                piece = CURRENT_BOARD[row][col]

                # Atualiza a peça exibida
                if piece != ".":
                    pixmap = QPixmap(PIECES[piece])
                    cell.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))
                else:
                    cell.setPixmap(QPixmap())


    def connect_to_lichess(self):
        """Connect to Lichess using the API token."""
        self.connect_dialog = ConnectWindow()
        self.connect_dialog.user_data.connect(self.handle_connection)
        self.connect_dialog.show()

    def handle_connection(self, data):
        global queue_thread
        self.current_token = data['token']
        if data['token'] is not None:
            self.status_label.setText(f"Connected as: {data['user']}")
            self.switch_layout(1)
            queue_thread = True
            thread = threading.Thread(target=self.stream_lichess_events, daemon=True)
            thread.start()
        else:
            self.status_label.setText(f"Status: failed to connected")
            queue_thread = False

    def new_game_lichess(self):
        self.search_a_game = SearchAGame(self.current_token)
        self.search_a_game.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = LichessInterface()
    window.show()

    sys.exit(app.exec())
