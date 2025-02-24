Tabuleiro de Xadrez Digital Low-Cost


Este repositório contém o código fonte do projeto de integração para o desenvolvimento de um tabuleiro de xadrez digital low-cost. O projeto integra:

Hardware: Um tabuleiro digital baseado em key matrices, que utiliza switches magnéticos e diodos para detectar a presença e movimento das peças, e um microcontrolador ESP32 para controlar um display LCD 16x2 via I2C.


Software: Uma interface gráfica desenvolvida em Python com PySide6, que se conecta à API do Lichess para transmitir e analisar os eventos das partidas (movimentos, tempos e resultados) e envia os dados via comunicação serial para o ESP32.
