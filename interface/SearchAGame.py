import threading
import time

import requests
from base_windows.search_a_game import Ui_Form
from PySide6.QtWidgets import (QDialog)
from PySide6.QtCore import Signal, QTimer

in_queue = False
stop_queue = False


class SearchAGame(QDialog, Ui_Form):
    def __init__(self, current_token) -> None:
        super(SearchAGame, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Search a Game')
        self.queue_ai.clicked.connect(self.challenge_ai)
        self.queue_player.clicked.connect(self.challenge_player)
        self.strenght_buttons = [self.strenght_1, self.strenght_2, self.strenght_3, self.strenght_4, self.strenght_5,
                                 self.strenght_6, self.strenght_7, self.strenght_8]
        self.ai_color_buttons = [self.random_color_ai, self.white_color_ai, self.black_color_ai]
        self.player_color_buttons = [self.random_color_player, self.white_color_player, self.black_color_player]
        self.random_color_player.setChecked(True)
        self.yes_rated.clicked.connect(self.rated_click)
        self.no_rated.clicked.connect(self.no_rated_click)
        self.setup_buttons()
        self.current_token = current_token
        self.spin_minutes_ai.setMinimum(3)
        self.cancel_queue.hide()
        self.wait_time.hide()
        self.wait_time_int = 0
        self.cancel_queue.clicked.connect(self.leave_queue)

    def rated_click(self):
        self.no_rated.setChecked(False)
        self.yes_rated.setChecked(True)

    def no_rated_click(self):
        self.no_rated.setChecked(True)
        self.yes_rated.setChecked(False)

    def setup_buttons(self):
        for button in self.strenght_buttons:
            button.clicked.connect(lambda checked, btn=button: self.uncheck_strength_buttons(btn))
        for button in self.ai_color_buttons:
            button.clicked.connect(lambda checked, btn=button: self.uncheck_ai_color_buttons(btn))
        for button in self.player_color_buttons:
            button.clicked.connect(lambda checked, btn=button: self.uncheck_player_color_buttons(btn))

    def challenge_ai(self):
        challenge_params = {'level': self.get_selected_level(),
                            'clock.limit': int(self.spin_minutes_ai.value()) * 60,
                            'clock.increment': self.spin_increments_ai.value(),
                            'color': self.get_ai_selected_color(),
                            'variant': 'standard'}
        print(challenge_params)
        response = requests.post("https://lichess.org/api/challenge/ai",
                                headers={"Authorization": f"Bearer {self.current_token}",
                                         "Content-Type": "application/x-www-form-urlencoded"},
                                data=challenge_params)


    def put_in_queue(self):
        global in_queue
        global stop_queue
        challenge_params = {'rated': str(self.get_rating_option()).lower(),
                            'time': int(self.spin_minutes_player.value()),
                            'increment': int(self.spin_increments_player.value()),
                            'color': self.get_player_selected_color(),
                            'variant': 'standard'}
        print(f'Iniciando o post request com os seguintes parâmetros: {challenge_params}')
        in_queue = True
        stop_queue = False
        with requests.post("https://lichess.org/api/board/seek",
                                headers={"Authorization": f"Bearer {self.current_token}",
                                         "Content-Type": "application/x-www-form-urlencoded"},
                                data=challenge_params, stream=True) as response:
            for line in enumerate(response.iter_lines()):
                if stop_queue is True:
                    break
                if line:
                    print(line)
        in_queue = False


    def challenge_player(self):
        global in_queue
        if not in_queue:
            self.queue_thread = threading.Thread(target=self.put_in_queue, daemon=True)
            self.queue_thread.start()
            self.cancel_queue.show()
            self.wait_time_int = 0
            self.wait_time.setText('0:00')
            self.wait_time.show()
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_time)
            self.timer.start(1000)


    def update_time(self):
        global in_queue
        if in_queue is False:
            self.leave_queue()
            return
        self.wait_time_int += 1
        minutes = self.wait_time_int // 60
        seconds = self.wait_time_int % 60
        self.wait_time.setText(f'{minutes}:{seconds:02d}')

    def leave_queue(self):
        global stop_queue
        global in_queue
        self.timer.stop()
        self.cancel_queue.hide()
        stop_queue = True
        self.wait_time.setText('Saindo da fila...')
        self.exit_timer = QTimer()
        self.exit_timer.timeout.connect(self.check_exit_queue)
        self.exit_timer.start(500)

    def check_exit_queue(self):
        global in_queue
        if not in_queue:
            self.exit_timer.stop()
            self.wait_time.hide()
    def get_ai_selected_color(self):
        for color in self.ai_color_buttons:
            if color.isChecked():
                return color.text().lower()

    def get_player_selected_color(self):
        for color in self.player_color_buttons:
            if color.isChecked():
                return color.text().lower()

    def get_rating_option(self):
        if self.yes_rated.isChecked():
            return True
        return False

    def get_selected_level(self):
        for button in self.strenght_buttons:
            if button.isChecked():
                return int(button.text())

    def uncheck_strength_buttons(self, clicked_button):
        for button in self.strenght_buttons:
            if button != clicked_button:
                button.setChecked(False)
        clicked_button.setChecked(True)

    def uncheck_ai_color_buttons(self, clicked_button):
        for button in self.ai_color_buttons:
            if button != clicked_button:
                button.setChecked(False)
        clicked_button.setChecked(True)

    def uncheck_player_color_buttons(self, clicked_button):
        for button in self.player_color_buttons:
            if button != clicked_button:
                button.setChecked(False)
        clicked_button.setChecked(True)

