import sys
import serial
import threading
import time
import copy
import json
import logging
import requests

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel,
                               QWidget, QGridLayout, QStackedLayout, QHBoxLayout, QFrame)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QPixmap

from ConnectWindow import ConnectWindow
from SearchAGame import SearchAGame
from ClockWidget import ClockWidget

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapeamento das peças para os caminhos das imagens
PIECES = {
    'P': 'interface/images/white-pawn.png',
    'p': 'interface/images/black-pawn.png',
    'R': 'interface/images/white-rook.png',
    'r': 'interface/images/black-rook.png',
    'N': 'interface/images/white-knight.png',
    'n': 'interface/images/black-knight.png',
    'B': 'interface/images/white-bishop.png',
    'b': 'interface/images/black-bishop.png',
    'Q': 'interface/images/white-queen.png',
    'q': 'interface/images/black-queen.png',
    'K': 'interface/images/white-king.png',
    'k': 'interface/images/black-king.png',
}

# Configuração inicial do tabuleiro (FEN simplificado)
INITIAL_BOARD = [
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
]

# =============================================================================
# Classe para gerenciar o estado do tabuleiro
# =============================================================================
class ChessBoard:
    """
    Gerencia o estado interno do tabuleiro de xadrez e operações relacionadas.
    """
    def __init__(self):
        self.state = copy.deepcopy(INITIAL_BOARD)
    
    def reset_board(self):
        """Reseta o tabuleiro para a posição inicial."""
        self.state = copy.deepcopy(INITIAL_BOARD)
    
    @staticmethod
    def letter_position(letter):
        """Converte uma letra (ex.: 'a') para um índice numérico (0 para 'a')."""
        return ord(letter.lower()) - ord('a')
    
    def apply_move(self, move):
        """
        Atualiza o estado do tabuleiro aplicando o movimento dado.
        Suporta roque, promoção e movimento normal.
        """
        start = move[:2]
        end = move[2:4]
        # Roque
        if start == 'e1' and end == 'g1' and self.state[7][4].upper() == 'K':
            self.state[7][6] = 'K'
            self.state[7][5] = 'R'
            self.state[7][4] = '.'
            self.state[7][7] = '.'
        elif start == 'e1' and end == 'c1' and self.state[7][4].upper() == 'K':
            self.state[7][2] = 'K'
            self.state[7][3] = 'R'
            self.state[7][4] = '.'
            self.state[7][0] = '.'
        elif start == 'e8' and end == 'g8' and self.state[0][4] == 'k':
            self.state[0][6] = 'k'
            self.state[0][5] = 'r'
            self.state[0][4] = '.'
            self.state[0][7] = '.'
        elif start == 'e8' and end == 'c8' and self.state[0][4] == 'k':
            self.state[0][2] = 'k'
            self.state[0][3] = 'r'
            self.state[0][4] = '.'
            self.state[0][0] = '.'
        # Promoção (movimento com 5 caracteres, ex.: "e7e8q")
        elif len(move) == 5:
            start_row = 8 - int(start[1])
            start_col = self.letter_position(start[0])
            end_row = 8 - int(end[1])
            end_col = self.letter_position(end[0])
            # Captura o peão que está se movendo para determinar sua cor
            pawn = self.state[start_row][start_col]
            self.state[start_row][start_col] = '.'
            if pawn.isupper():
                # Peão branco: converte para maiúscula
                promoted_piece = move[4].upper()
            else:
                # Peão preto: mantém minúsculo
                promoted_piece = move[4].lower()
            self.state[end_row][end_col] = promoted_piece
        else:
            # Movimento normal
            start_row = 8 - int(start[1])
            start_col = self.letter_position(start[0])
            end_row = 8 - int(end[1])
            end_col = self.letter_position(end[0])
            self.state[end_row][end_col] = self.state[start_row][start_col]
            self.state[start_row][start_col] = '.'
    
    def translate_move(self, move):
        """
        Converte um movimento no formato UCI para uma notação simplificada.
        Essa tradução é simplificada e pode não cobrir todos os casos.
        """
        start = move[:2]
        end = move[2:4]
        promotion = move[4] if len(move) == 5 else None
        
        # Roque
        if start == 'e1' and end == 'g1' and self.state[7][4].upper() == 'K':
            return 'O-O'
        elif start == 'e1' and end == 'c1' and self.state[7][4].upper() == 'K':
            return 'O-O-O'
        elif start == 'e8' and end == 'g8' and self.state[0][4] == 'k':
            return 'O-O'
        elif start == 'e8' and end == 'c8' and self.state[0][4] == 'k':
            return 'O-O-O'
        
        start_row = 8 - int(start[1])
        start_col = self.letter_position(start[0])
        end_row = 8 - int(end[1])
        end_col = self.letter_position(end[0])
        moving_piece = self.state[start_row][start_col]
        target_piece = self.state[end_row][end_col]
        
        # Promoção
        if promotion:
            if target_piece != '.':
                return f"{start[0]}x{end}={promotion.upper() if moving_piece.isupper() else promotion.lower()}"
            else:
                return f"{end}={promotion.upper() if moving_piece.isupper() else promotion.lower()}"
        
        # Movimento de peão
        if moving_piece.lower() == 'p':
            if target_piece != '.':
                return f"{start[0]}x{end}"
            else:
                return f"{end}"
        else:
            piece_letter = moving_piece.upper() if moving_piece != '.' else ''
            if target_piece != '.':
                return f"{piece_letter}x{end}"
            else:
                return f"{piece_letter}{end}"

# =============================================================================
# Threads para streaming dos eventos do Lichess
# =============================================================================
class LichessEventStreamThread(QThread):
    """
    Thread para streaming de eventos gerais do Lichess.
    """
    event_received = Signal(dict)
    error = Signal(str)
    
    def __init__(self, token, parent=None):
        super().__init__(parent)
        self.token = token
        self._running = True
    
    def run(self):
        url = "https://lichess.org/api/stream/event"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            with requests.get(url, headers=headers, stream=True) as response:
                if response.status_code != 200:
                    self.error.emit(f"Erro: HTTP {response.status_code}")
                    return
                for line in response.iter_lines():
                    if not self._running:
                        break
                    if line:
                        try:
                            event = json.loads(line)
                            self.event_received.emit(event)
                        except Exception as e:
                            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        self._running = False

class LichessGameStreamThread(QThread):
    """
    Thread para streaming dos eventos de um jogo específico.
    """
    event_received = Signal(dict)
    error = Signal(str)
    
    def __init__(self, token, game_id, parent=None):
        super().__init__(parent)
        self.token = token
        self.game_id = game_id
        self._running = True
    
    def run(self):
        url = f"https://lichess.org/api/board/game/stream/{self.game_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            with requests.get(url, headers=headers, stream=True) as response:
                if response.status_code != 200:
                    self.error.emit(f"Erro: HTTP {response.status_code}")
                    return
                for line in response.iter_lines():
                    if not self._running:
                        break
                    if line:
                        try:
                            event = json.loads(line)
                            self.event_received.emit(event)
                        except Exception as e:
                            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        self._running = False

# =============================================================================
# Classe principal da interface gráfica
# =============================================================================
class LichessInterface(QMainWindow):
    """
    Interface gráfica para interagir com a API do Lichess.
    """
    start_timer_signal = Signal()
    stop_timer_signal = Signal()  # Sinal para parar o timer
    game_start_signal = Signal()
    game_finish_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lichess Interface")
        self.setGeometry(100, 100, 460, 600)
        self.setMaximumWidth(460)
        self.setMaximumHeight(600)
        self.setWindowIcon(QPixmap('images/black-knight.png'))
        self.game_active = False  # Flag para controle do jogo

        # Variáveis de controle
        self.current_token = None
        self.current_game = None
        self.current_color = 'white'
        self.to_move = 'white'
        self.current_moves = 0
        
        # Instância do tabuleiro
        self.chess_board = ChessBoard()
        
        # Threads de streaming
        self.event_thread = None
        self.game_thread = None
        
        # Configuração da interface gráfica
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)
        
        # Header: layout empilhado e relógios
        self.top_header = QFrame()
        self.top_header_layout = QHBoxLayout(self.top_header)
        self.layout.addWidget(self.top_header)
        
        self.misc_layout = QStackedLayout()
        self.top_header_layout.addLayout(self.misc_layout)
        
        self.opponent_time = ClockWidget()
        self.top_header_layout.addWidget(self.opponent_time)
        self.opponent_time.hide()
        
        # Layouts para diferentes estados (conectar, conectado, em jogo)
        self.connect_layout = self.create_connect_layout()
        self.connected_layout = self.create_connected_layout()
        self.in_game_layout = self.create_in_game_layout()
        self.misc_layout.addWidget(self.connect_layout)
        self.misc_layout.addWidget(self.connected_layout)
        self.misc_layout.addWidget(self.in_game_layout)
        self.switch_layout(0)
        
        # Tabuleiro gráfico
        self.board_widget = QWidget()
        self.board_layout = QGridLayout()
        self.board_widget.setLayout(self.board_layout)
        self.layout.addWidget(self.board_widget)
        self.cells = []
        self.initialize_board()
        
        # Relógios
        self.your_time = ClockWidget()
        self.clock_layout = QHBoxLayout()
        self.clock_layout.addStretch()
        self.clock_layout.addWidget(self.your_time)
        self.layout.addLayout(self.clock_layout)
        self.your_time.hide()
        
        # Timer para atualizar os relógios
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.update_time)
        
        # Conexões de sinais
        self.start_timer_signal.connect(self.start_timer_main_thread)
        self.stop_timer_signal.connect(self.stop_timer_main_thread)
        self.resign_button.clicked.connect(self.resign)
        self.game_start_signal.connect(self.your_time.show)
        self.game_start_signal.connect(self.opponent_time.show)
        self.game_start_signal.connect(lambda: self.switch_layout(2))
        self.game_finish_signal.connect(self.your_time.hide)
        self.game_finish_signal.connect(self.opponent_time.hide)

        # Inicialize a porta serial (ajuste o COM e baud rate conforme necessário)
        self.serial_port = serial.Serial('COM9', 115200, timeout=1)
        # Inicia uma thread para enviar atualizações do relógio
        self.start_serial_thread()
    
    def create_connect_layout(self):
        """Cria o layout de conexão com o Lichess."""
        widget = QWidget()
        self.connect_button = QPushButton("Connect to Lichess")
        self.connect_button.clicked.connect(self.connect_to_lichess)
        layout = QVBoxLayout(widget)
        layout.addWidget(self.connect_button)
        return widget
    
    def create_connected_layout(self):
        """Cria o layout para o estado conectado."""
        widget = QWidget()
        self.result_label = QLabel("Result: --")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.new_game_button = QPushButton("New game")
        self.new_game_button.clicked.connect(self.new_game_lichess)
        layout = QVBoxLayout(widget)
        layout.addWidget(self.result_label)
        layout.addWidget(self.new_game_button)
        return widget
    
    def create_in_game_layout(self):
        """Cria o layout exibido durante a partida."""
        widget = QWidget()
        self.resign_button = QPushButton("Resign")
        self.opponent = QLabel("Unknown (00)")
        self.last_move = QLabel("--")
        layout = QHBoxLayout(widget)
        layout.addWidget(self.resign_button)
        layout.addWidget(self.opponent)
        layout.addWidget(self.last_move)
        widget.setMinimumWidth(100)
        return widget
    
    def switch_layout(self, index):
        """Alterna entre os layouts empilhados."""
        self.misc_layout.setCurrentIndex(index)
    
    def initialize_board(self):
        """
        Cria o tabuleiro gráfico (8x8) com células representadas por QLabel.
        """
        self.game_active = True
        self.cells = []  # Reinicia a lista de células
        for row in range(8):
            row_cells = []
            for col in range(8):
                cell = QLabel()
                cell.setFixedSize(50, 50)
                cell.setAlignment(Qt.AlignCenter)
                # Células com cores alternadas
                if (row + col) % 2 == 0:
                    cell.setStyleSheet("background-color: white; border: 1px solid black;")
                else:
                    cell.setStyleSheet("background-color: grey; border: 1px solid black;")
                self.board_layout.addWidget(cell, row, col)
                row_cells.append(cell)
            self.cells.append(row_cells)
        self.update_board()
    
    def update_board(self):
        """
        Atualiza as imagens do tabuleiro com base no estado atual armazenado em self.chess_board.
        Se o jogador for preto, inverte a exibição.
        """
        for row in range(8):
            for col in range(8):
                if self.current_color == 'black':
                    cell = self.cells[7 - row][7 - col]
                else:
                    cell = self.cells[row][col]
                piece = self.chess_board.state[row][col]
                if piece != ".":
                    pixmap = QPixmap(PIECES.get(piece, ""))
                    cell.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))
                else:
                    cell.setPixmap(QPixmap())
    
    def connect_to_lichess(self):
        """Abre a janela de conexão para inserir o token do Lichess."""
        self.connect_dialog = ConnectWindow()
        self.connect_dialog.user_data.connect(self.handle_connection)
        self.connect_dialog.show()
    
    def handle_connection(self, data):
        """
        Trata os dados recebidos da janela de conexão.
        Se o token for válido, inicia o streaming de eventos.
        """
        self.current_token = data.get('token')
        if self.current_token:
            self.status_label.setText(f"Connected as: {data.get('user')}")
            self.switch_layout(1)
            # Inicia o streaming de eventos gerais
            self.event_thread = LichessEventStreamThread(self.current_token)
            self.event_thread.event_received.connect(self.handle_event)
            self.event_thread.error.connect(self.handle_error)
            self.event_thread.start()
        else:
            self.status_label.setText("Status: failed to connect")
    
    def handle_event(self, event):
        """
        Processa os eventos gerais do Lichess.
        Em 'gameStart', inicia o streaming dos eventos do jogo.
        Em 'gameFinish', trata o término da partida.
        """
        event_type = event.get('type')
        if event_type == 'gameStart':
            self.game_start_signal.emit()
            self.current_moves = 0
            game_info = event.get('game', {})
            if game_info.get('source') != 'ai':
                opponent_info = game_info.get('opponent', {})
                self.opponent.setText(f"{opponent_info.get('username', 'Unknown')} ({opponent_info.get('rating', '00')})")
            else:
                self.opponent.setText(f"{game_info.get('opponent', {}).get('username', 'Unknown')}")
            self.current_game = game_info.get('gameId')
            self.current_color = game_info.get("color", "white")
            self.last_move.setText('--')
            self.your_time.setText('--:--')
            self.opponent_time.setText('--:--')
            self.chess_board.reset_board()
            self.update_board()
            # Inicia o streaming dos eventos do jogo
            self.game_thread = LichessGameStreamThread(self.current_token, self.current_game)
            self.game_thread.event_received.connect(self.handle_game_events)
            self.game_thread.error.connect(self.handle_error)
            self.game_thread.start()
        elif event_type == 'gameFinish':
            self.stop_timer_signal.emit()
            self.game_finish_signal.emit()
            self.switch_layout(1)
            self.game_active = False  # Jogo finalizado, não atualizar mais os relógios

            game_data = event.get('game', {})
            status = game_data.get('status', {}).get('name', '')
            if status != 'aborted':
                if 'winner' not in game_data:
                    self.result_label.setText('1/2-1/2')
                elif game_data.get('winner') == 'black':
                    self.result_label.setText('0-1')
                elif game_data.get('winner') == 'white':
                    self.result_label.setText('1-0')
                else:
                    self.result_label.setText('1/2-1/2')
            else:
                self.result_label.setText('Aborted')
            self.current_game = None
            if self.game_thread:
                self.game_thread.stop()
                self.game_thread.wait()
                self.game_thread = None
    
    def handle_game_events(self, event):
        """
        Processa os eventos do jogo:
          - Atualiza o tabuleiro aplicando o último movimento.
          - Atualiza os relógios e exibe a notação do último movimento.
        """
        # Se a partida já terminou, não processa novos eventos
        if self.current_game is None:
            return
        try:
            if event.get('type') == 'gameState':
                moves_str = event.get('moves', "")
                moves_list = moves_str.split()
                if moves_list:
                    last_move = moves_list[-1]
                    self.current_moves += 1
                    translated_move = self.chess_board.translate_move(last_move)
                    self.chess_board.apply_move(last_move)
                    self.last_move.setText(f"{translated_move}")
                    self.update_board()
                white_time = event.get('wtime', 0) / 1000
                black_time = event.get('btime', 0) / 1000
                if len(moves_list) % 2 == 0:
                    self.to_move = 'white'
                else:
                    self.to_move = 'black'
                if self.current_color == 'white':
                    self.your_time.setText(f"{int(white_time/60):02d}:{int(white_time%60):02d}")
                    self.opponent_time.setText(f"{int(black_time/60):02d}:{int(black_time%60):02d}")
                else:
                    self.your_time.setText(f"{int(black_time/60):02d}:{int(black_time%60):02d}")
                    self.opponent_time.setText(f"{int(white_time/60):02d}:{int(white_time%60):02d}")
                if len(moves_list) >= 2:
                    self.start_timer_signal.emit()
                self.game_active = True
        except Exception as e:
            logger.error(f"Error in handle_game_events: {e}")
    
    def start_timer_main_thread(self):
        """Inicia o timer para atualização dos relógios a cada segundo."""
        self.move_timer.start(1000)
    
    def stop_timer_main_thread(self):
        """Para o timer (executado na thread principal)."""
        self.move_timer.stop()
    
    def update_time(self):
        """Atualiza os relógios decrementando 1 segundo a cada tick do timer."""
        if not self.game_active:
            return
        try:
            if self.to_move == 'white' and self.current_color == 'white':
                time_text = self.your_time.text()
                if not time_text[0].isdigit():
                    return
                minutes, seconds = map(int, time_text.split(':'))
                total_seconds = minutes * 60 + seconds - 1
                self.your_time.setText(f"{int(total_seconds/60):02d}:{int(total_seconds%60):02d}")
            else:
                time_text = self.opponent_time.text()
                if not time_text[0].isdigit():
                    return
                minutes, seconds = map(int, time_text.split(':'))
                total_seconds = minutes * 60 + seconds - 1
                self.opponent_time.setText(f"{int(total_seconds/60):02d}:{int(total_seconds%60):02d}")
        except Exception as e:
            logger.error(f"Error in update_time: {e}")
    
    def resign(self):
        """
        Envia uma requisição para desistir ou abortar o jogo,
        conforme o estado atual dos lances.
        """
        if not self.current_game:
            return
        if self.current_color == 'white' and self.current_moves == 0:
            endpoint = "abort"
        elif self.current_color == 'black' and self.current_moves == 1:
            endpoint = "abort"
        else:
            endpoint = "resign"
        url = f"https://lichess.org/api/board/game/{self.current_game}/{endpoint}"
        try:
            response = requests.post(url, headers={"Authorization": f"Bearer {self.current_token}"})
            if response.status_code != 200:
                logger.error("Falha ao enviar desistência ou abortar o jogo.")
        except Exception as e:
            logger.error(f"Error in resign: {e}")
    
    def new_game_lichess(self):
        """Inicia uma nova partida no Lichess."""
        self.your_time.hide()
        self.search_a_game = SearchAGame(self.current_token)
        self.game_start_signal.connect(self.search_a_game.close)
        self.search_a_game.show()
    
    def handle_error(self, error_message):
        """Trata erros emitidos pelas threads de streaming."""
        logger.error(f"Stream error: {error_message}")
        
    def start_serial_thread(self):
        thread = threading.Thread(target=self.serial_update_loop, daemon=True)
        thread.start()
    
    def serial_update_loop(self):
        # Essa thread é executada em background, enviando os tempos a cada segundo
        while True:
            if self.game_active:
                white_time_str = self.your_time.text()   # Ex: "02:59"
                black_time_str = self.opponent_time.text() # Ex: "02:59"
                last_move_val = self.last_move.text().replace("x", "")
                msg = f"{white_time_str};{last_move_val};{black_time_str}"
            else:
                result = self.result_label.text()  # Ex: "1-0", "0-1" ou "1/2-1/2"
                msg = f".......{result}......."
            try:
                self.serial_port.write(msg.encode())
            except Exception as e:
                print("Erro enviando via serial:", e)
            time.sleep(1)

# =============================================================================
# Execução principal
# =============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LichessInterface()
    window.show()
    sys.exit(app.exec())
