/* UART asynchronous example, that uses separate RX and TX tasks

   This example code is in the Public Domain (or CC0 licensed, at your option.)

   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "driver/uart.h"
#include "string.h"
#include "stdio.h"
#include "stdlib.h"
#include "driver/gpio.h"
#include "freertos/queue.h"
#include <inttypes.h>
#include <string.h>
#include <math.h>
#include "driver/i2c.h"
#include <stdint.h>

extern void esp_rom_delay_us(uint32_t us);

#define BUTTON_PIN GPIO_NUM_23
volatile bool buttonPressed = false;
bool move_valid = false;              
char last_move[10];
char current_move[10];       
char last_valid_board[8][8];
#define BOARD_SIZE 8
#define entrada  ((1ULL << 14) | (1ULL << 25) | (1ULL << 26) | (1ULL << 27) | (1ULL << 32) | (1ULL << 33) | (1ULL << 34) | (1ULL << 35))
#define saidas  ((1ULL << 15) | (1ULL << 2) | (1ULL << 4) | (1ULL << 16) | (1ULL << 17) | (1ULL << 5) | (1ULL << 18) | (1ULL << 19) | (1ULL << 12) | (1ULL << 13))
#define UART_NUM            UART_NUM_0
#define UART_TX_PIN         GPIO_NUM_1   // ajuste conforme sua ligação
#define UART_RX_PIN         GPIO_NUM_3   // ajuste conforme sua ligação
#define UART_BUF_SIZE       1024

// Configurações do I2C e LCD (como no exemplo anterior)
#define I2C_MASTER_NUM              I2C_NUM_0
#define I2C_MASTER_SDA_IO           GPIO_NUM_21
#define I2C_MASTER_SCL_IO           GPIO_NUM_22
#define I2C_MASTER_FREQ_HZ          400000
#define LCD_ADDR                    0x27
#define I2C_MASTER_RX_BUF_DISABLE   0
#define I2C_MASTER_TX_BUF_DISABLE   0


#define LCD_RS         (1 << 0)
#define LCD_RW         (1 << 1)
#define LCD_EN         (1 << 2)
#define LCD_BACKLIGHT  (1 << 3)

// Comandos do HD44780
#define LCD_CMD_CLEAR           0x01
#define LCD_CMD_RETURN_HOME     0x02
#define LCD_CMD_ENTRY_MODE      0x04
#define LCD_CMD_DISPLAY_CTRL    0x08
#define LCD_CMD_FUNCTION_SET    0x20

#define LCD_ENTRY_LEFT         0x02
#define LCD_DISPLAY_ON         0x04
#define LCD_2LINE              0x08
#define LCD_5x8DOTS            0x00

static const char *TAG = "CHESS_CLOCK";

// Inicializa o barramento I2C
esp_err_t i2c_master_init(void)
{
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };
    esp_err_t ret = i2c_param_config(I2C_MASTER_NUM, &conf);
    if (ret != ESP_OK) return ret;
    return i2c_driver_install(I2C_MASTER_NUM, conf.mode, I2C_MASTER_RX_BUF_DISABLE, I2C_MASTER_TX_BUF_DISABLE, 0);
}

// Envia um byte para o módulo PCF8574 via I2C
esp_err_t lcd_write_byte(uint8_t data)
{
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    ESP_ERROR_CHECK(i2c_master_start(cmd));
    ESP_ERROR_CHECK(i2c_master_write_byte(cmd, (LCD_ADDR << 1) | I2C_MASTER_WRITE, true));
    ESP_ERROR_CHECK(i2c_master_write_byte(cmd, data, true));
    ESP_ERROR_CHECK(i2c_master_stop(cmd));
    esp_err_t ret = i2c_master_cmd_begin(I2C_MASTER_NUM, cmd, pdMS_TO_TICKS(1000));
    i2c_cmd_link_delete(cmd);
    return ret;
}

// Envia um pulso de Enable (E)
void lcd_pulse_enable(void)
{
    // Ativa E, aguarda 1us e desativa E
    lcd_write_byte(LCD_BACKLIGHT | LCD_EN);
    esp_rom_delay_us(2);
    lcd_write_byte(LCD_BACKLIGHT);
    esp_rom_delay_us(50);
}

// Envia um nibble (4 bits) para o LCD com controle (RS = 0 para comando, RS = 1 para dados)
esp_err_t lcd_send_nibble(uint8_t nibble, uint8_t control)
{
    uint8_t data = ((nibble & 0x0F) << 4) | control | LCD_BACKLIGHT;
    esp_err_t ret = lcd_write_byte(data | LCD_EN);
    vTaskDelay(pdMS_TO_TICKS(2));
    ret |= lcd_write_byte(data & ~LCD_EN);
    vTaskDelay(pdMS_TO_TICKS(2));
    return ret;
}

// Envia um byte (dividido em dois nibbles) para o LCD
esp_err_t lcd_send_byte(uint8_t byte, uint8_t rs)
{
    esp_err_t ret = lcd_send_nibble(byte >> 4, rs ? LCD_RS : 0);
    ret |= lcd_send_nibble(byte & 0x0F, rs ? LCD_RS : 0);
    return ret;
}

// Envia um comando ao LCD
void lcd_command(uint8_t cmd)
{
    lcd_send_byte(cmd, 0);
    vTaskDelay(pdMS_TO_TICKS(5));
}

// Envia um caractere (dado) ao LCD
void lcd_data(uint8_t data)
{
    lcd_send_byte(data, LCD_RS);
    vTaskDelay(pdMS_TO_TICKS(5));
}

// Inicializa o LCD (sequência de 4 bits)
void lcd_init(void)
{
    // Aguarda 50ms para estabilização
    vTaskDelay(pdMS_TO_TICKS(50));

    // Sequência de inicialização conforme datasheet do HD44780:
    lcd_send_nibble(0x03, 0);
    vTaskDelay(pdMS_TO_TICKS(10));
    lcd_send_nibble(0x03, 0);
    vTaskDelay(pdMS_TO_TICKS(10));
    lcd_send_nibble(0x03, 0);
    vTaskDelay(pdMS_TO_TICKS(10));
    // Muda para modo 4 bits:
    lcd_send_nibble(0x02, 0);
    vTaskDelay(pdMS_TO_TICKS(10));

    // Função: 4 bits, 2 linhas, fonte 5x8
    lcd_command(LCD_CMD_FUNCTION_SET | LCD_2LINE | LCD_5x8DOTS);
    // Liga o display (sem cursor nem blink)
    lcd_command(LCD_CMD_DISPLAY_CTRL | LCD_DISPLAY_ON);
    // Limpa o display
    lcd_command(LCD_CMD_CLEAR);
    vTaskDelay(pdMS_TO_TICKS(10));
    // Configura o modo de entrada: incremento automático
    lcd_command(LCD_CMD_ENTRY_MODE | LCD_ENTRY_LEFT);
    vTaskDelay(pdMS_TO_TICKS(10));

    ESP_LOGI(TAG, "LCD I2C inicializado");
}

// Limpa o display
void lcd_clear(void)
{
    lcd_command(LCD_CMD_CLEAR);
    vTaskDelay(pdMS_TO_TICKS(10));
}

// Posiciona o cursor (coluna e linha)
void lcd_set_cursor(uint8_t col, uint8_t row)
{
    uint8_t row_offsets[] = {0x00, 0x40};
    lcd_command(0x80 | (col + row_offsets[row]));
}

// Escreve uma string no LCD
void lcd_write_string(const char *str)
{
    while (*str) {
        lcd_data((uint8_t)*str++);
    }
}

void reset_board(){
    char whitePieces[] = {'R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'};
    char blackPieces[] = {'r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'};
    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            if (i == 0) { 
                last_valid_board[i][j] = whitePieces[j];
            } else if (i == 1) { 
                last_valid_board[i][j] = 'P';
            } else if (i == 6) { 
                last_valid_board[i][j] = 'p';
            } else if (i == 7) { 
                last_valid_board[i][j] = blackPieces[j];
            } else {
                last_valid_board[i][j] = '.';
            }
        }
    }
}

// Função para atualizar o display com os tempos recebidos
void update_lcd_clock(const char *msg) {
    char msg_winner[64];
    if (strcmp(msg, "reset") == 1){
        reset_board();
        return;
    }
    if (strchr(msg, ';') == NULL) {
        lcd_clear();
        strncpy(msg_winner, msg, sizeof(msg_winner)-1);
        int len = strlen(msg_winner);
        // Calcula posição para centralizar o resultado (display de 16 colunas)
        int pos = (16 - len) / 2;
        lcd_set_cursor(4, 0);
        lcd_write_string("GAME OVER");
        lcd_set_cursor(pos, 1);
        lcd_write_string(msg_winner);
        reset_board();
        return;
    }
    // Espera-se o formato: "white_time;last_move;black_time;last_move_uci"
    char header[21];
    char line2[21];
    char msg_copy[64];
    strncpy(msg_copy, msg, sizeof(msg_copy)-1);
    msg_copy[sizeof(msg_copy)-1] = '\0';
    
    // Usa strtok para separar os tokens
    char *token = strtok(msg_copy, ";");
    if (token != NULL) {
        char white_time[10];
        strncpy(white_time, token, sizeof(white_time)-1);
        white_time[sizeof(white_time)-1] = '\0';
    
        token = strtok(NULL, ";");
        if (token != NULL) {
            char last_move_lichess[10];
            strncpy(last_move_lichess, token, sizeof(last_move_lichess)-1);
            last_move_lichess[sizeof(last_move_lichess)-1] = '\0';
    
            token = strtok(NULL, ";");
            if (token != NULL) {
                char black_time[10];
                strncpy(black_time, token, sizeof(black_time)-1);
                black_time[sizeof(black_time)-1] = '\0';
    
                // Atualiza o display apenas com os tokens referentes aos tempos e último movimento lichess
                snprintf(header, sizeof(header), "WHITE  LM  BLACK");
                snprintf(line2, sizeof(line2), "%5.5s %-3.3s  %5.5s", white_time, last_move_lichess, black_time);
    
                lcd_clear();
                lcd_set_cursor(0,0);
                lcd_write_string(header);
                lcd_set_cursor(0,1);
                lcd_write_string(line2);
    
                // Pega o quarto token para atualizar somente o tabuleiro
                token = strtok(NULL, ";");
                if (token != NULL) {
                    if (strcmp (token, "None") == 0){

                    if (strcmp(token, last_move) != 0) {
                        int src_letter = token[0] - 'a';        // 'a' -> 0, 'b' -> 1, etc.
                        int src_digit  = (token[1] - '0') - 1;    // '3' -> 3 - 1 = 2
                        int dst_letter = token[2] - 'a';
                        int dst_digit  = (token[3] - '0') - 1;            
                        last_valid_board[dst_digit][dst_letter] = last_valid_board[src_digit][src_letter];
                        last_valid_board[src_digit][src_letter] = '.';
                        gpio_set_level(GPIO_NUM_12, 1);
                        gpio_set_level(GPIO_NUM_13, 0);
                        move_valid = false; 
                        strcpy(last_move, token);
                    }
                }
                else{
                    reset_board();
                }
                }
                return; // Processamento concluído com sucesso
            }
        }
    }
    // Se o formato não for o esperado, mostra a mensagem completa na primeira linha
    lcd_clear();
    lcd_set_cursor(0,0);
    lcd_write_string(msg);
}

// Tarefa para receber dados pela UART e atualizar o LCD
void uart_rx_task(void *pvParameters)
{
    uint8_t *data = (uint8_t *) malloc(UART_BUF_SIZE);
    while (1) {
        int len = uart_read_bytes(UART_NUM, data, UART_BUF_SIZE - 1, pdMS_TO_TICKS(1000));
        if (len > 0) {
            data[len] = '\0';
            ESP_LOGI(TAG, "Recebido: %s", (char *)data);
            update_lcd_clock((char *)data);
        }
    }
    free(data);
}

void uart_init_config(void)
{
    const uart_config_t uart_config = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE
    };
    uart_param_config(UART_NUM, &uart_config);
    uart_set_pin(UART_NUM, UART_TX_PIN, UART_RX_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uart_driver_install(UART_NUM, UART_BUF_SIZE * 2, 0, 0, NULL, 0);
}


void IRAM_ATTR buttonISR(void* arg) {
    buttonPressed = true;
}


void setup_interrupt(void){
    gpio_config_t conf_gpio={};  
    conf_gpio.intr_type = GPIO_INTR_DISABLE;           
    conf_gpio.mode = GPIO_MODE_OUTPUT;        
    conf_gpio.pin_bit_mask = saidas;
    conf_gpio.pull_down_en = 1;
    conf_gpio.pull_up_en = 0;                                           
    gpio_config(&conf_gpio);                             
    conf_gpio.intr_type = GPIO_INTR_DISABLE; 
    conf_gpio.mode = GPIO_MODE_INPUT;    
    conf_gpio.pin_bit_mask = entrada;
    conf_gpio.pull_down_en = 1;
    conf_gpio.pull_up_en = 0;                                           
    gpio_config(&conf_gpio);
    gpio_config_t io_conf = {};
    io_conf.intr_type = GPIO_INTR_POSEDGE;   // Interrupção na borda de subida (quando o pino vai de 0 para 1)
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pin_bit_mask = (1ULL << BUTTON_PIN);
    io_conf.pull_down_en = 1;
    io_conf.pull_up_en = 0;
    gpio_config(&io_conf);
    gpio_install_isr_service(0);
    gpio_isr_handler_add(BUTTON_PIN, buttonISR, NULL);
}


void print_board(int board[8][8]) {
    char columns_names[] = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'};

    printf("  ");
    for (int i = 0; i < 8; i++) {
        printf(" %c ", columns_names[i]);
    }
    printf("\n");

    for (int j = 0; j < 8; j++) {
        printf("%d ", j + 1);
        for (int i = 0; i < 8; i++) {
            printf(" %d ", board[j][i]);
        }
        printf("\n");
    }

    printf("  ");
    for (int i = 0; i < 8; i++) {
        printf(" %c ", columns_names[i]);
    }
    printf("\n");
}

void clean_change_list(char list[], int size) {
    memset(list, '\0', size);
}


int path_clear(int current_board[BOARD_SIZE][BOARD_SIZE], int src_row, int src_col, int dst_row, int dst_col) {
    int dr = dst_row - src_row;
    int dc = dst_col - src_col;
    int step_r = (dr == 0) ? 0 : (dr > 0 ? 1 : -1);
    int step_c = (dc == 0) ? 0 : (dc > 0 ? 1 : -1);
    
    int r = src_row + step_r;
    int c = src_col + step_c;
    while (r != dst_row || c != dst_col) {
        if (current_board[r][c] != 0)
            return 0;
        r += step_r;
        c += step_c;
    }
    return 1;
}

int is_valid_move(char piece, int src_row, int src_col, int dst_row, int dst_col,
                  int current_board[BOARD_SIZE][BOARD_SIZE]) {
    int dr = dst_row - src_row;
    int dc = dst_col - src_col;
    int abs_dr = abs(dr);
    int abs_dc = abs(dc);
    int isWhite = (piece >= 'A' && piece <= 'Z');
    
    
    if (piece == 'p' || piece == 'P') {
        if (piece == 'p') {
            // Peão PRETO: move para CIMA (linha diminui)
            if ((dr == -1 && dc == 0 && last_valid_board[dst_row][dst_col] == '.') || 
                (dr == -2 && src_row == 6 && dc == 0 && 
                 last_valid_board[dst_row][dst_col] == '.')){
                return 1;
            }
            // Captura para peão preto (diagonal para CIMA)
            if (dr == -1 && abs_dc == 1) {
                char target = last_valid_board[dst_row][dst_col];
                if (target != '.' && target >= 'A' && target <= 'Z') {
                    return 1;
                }
            }
        } else { // Peão BRANCO ('P')
            // Peão BRANCO: move para BAIXO (linha aumenta)
            if ((dr == 1 && dc == 0 && last_valid_board[dst_row][dst_col] == '.') || 
                (dr == 2 && src_row == 1 && dc == 0 && 
                    last_valid_board[dst_row][dst_col] == '.')) {
                return 1;
            }
            // Captura para peão branco (diagonal para BAIXO)
            if (dr == 1 && abs_dc == 1) {
                char target = last_valid_board[dst_row][dst_col];
                if (target != '.' && target >= 'a' && target <= 'z') {
                    return 1;
                }
            }
        }
        printf("dr == %i && dc == %i && current_board[%i][%i] == %i || dr == %i && src_row == %i && dc == %i && current_board[%i][%i] == %i && current_board[%i + 1][%i] == %i", dr, dc, dst_row, dst_col, current_board[dst_row][dst_col], dr, src_row, dc, dst_row, dst_col, current_board[dst_row][dst_col], src_row, src_col, current_board[src_row + 1][src_col]);
        return 0;
    }
    if (piece == 'r' || piece == 'R') {
        if (dr == 0 || dc == 0) {
            if (path_clear(current_board, src_row, src_col, dst_row, dst_col))
                return 1;
        }
        return 0;
    }
    
    if (piece == 'n' || piece == 'N') {
        if ((abs_dr == 2 && abs_dc == 1) || (abs_dr == 1 && abs_dc == 2))
            return 1;
        return 0;
    }
    
    if (piece == 'b' || piece == 'B') {
        if (abs_dr == abs_dc) {
            if (path_clear(current_board, src_row, src_col, dst_row, dst_col))
                return 1;
        }
        return 0;
    }
    
    if (piece == 'q' || piece == 'Q') {
        if ((dr == 0 || dc == 0) || (abs_dr == abs_dc)) {
            if (path_clear(current_board, src_row, src_col, dst_row, dst_col))
                return 1;
        }
        return 0;
    }
    
    if (piece == 'k' || piece == 'K') {
        if (abs_dr <= 1 && abs_dc <= 1)
            return 1;
        return 0;
    }
    
    return 0;
}

int verify_valid_board(int current_board[8][8], int num_adds, int number_of_removes, char addList[], char removeList[]){
    // first element equals line, second equals column
    char columns_names[] = {'a','b','c','d','e','f','g','h'};
    if (number_of_removes != num_adds){
        return 0;
    }
    if (num_adds > 2){
        return 0;
    }
    if (num_adds == 0){
        return 1;
    }
    if (num_adds == 1){
        int src_row = removeList[0] - '0';
        int src_col = removeList[1] - '0';
        int dst_row = addList[0] - '0';
        int dst_col = addList[1] - '0';
        char piece = last_valid_board[src_row][src_col];
        if (current_board[src_row][src_col] != 0 || current_board[dst_row][dst_col] != 1)
        return 0;
    
        if (piece == '.')
            return 0;
    
        if (!is_valid_move(piece, src_row, src_col, dst_row, dst_col, current_board))
            return 0;
        if ((piece == 'p') && src_row == 6 && dst_row == 7){
            sprintf(current_move, "%c%d%c%d", 
                columns_names[src_col], src_row + 1, 
                columns_names[dst_col], dst_row + 1);
        }
        else if ((piece == 'P') && src_row == 1 && dst_row == 0){
            sprintf(current_move, "%c%d%c%d", 
                columns_names[src_col], src_row + 1, 
                columns_names[dst_col], dst_row + 1);
        }
        else{
        sprintf(current_move, "%c%d%c%d", 
                columns_names[src_col], src_row + 1, 
                columns_names[dst_col], dst_row + 1);
        }
        return 1;
    }
    if (num_adds == 2) {
        int rem1_row = removeList[0] - '0';
        int rem1_col = removeList[1] - '0';
        int rem2_row = removeList[2] - '0';
        int rem2_col = removeList[3] - '0';

        int add1_row = addList[0] - '0';
        int add1_col = addList[1] - '0';
        int add2_row = addList[2] - '0';
        int add2_col = addList[3] - '0';

        if (current_board[rem1_row][rem1_col] != 0 ||
            current_board[rem2_row][rem2_col] != 0 ||
            current_board[add1_row][add1_col] != 1 ||
            current_board[add2_row][add2_col] != 1)
            return 0;

        int king_rem_index = 0, rook_rem_index = 0;
        int isRem1King = (last_valid_board[rem1_row][rem1_col] == 'K' ||
                          last_valid_board[rem1_row][rem1_col] == 'k');
        int isRem2King = (last_valid_board[rem2_row][rem2_col] == 'K' ||
                          last_valid_board[rem2_row][rem2_col] == 'k');

        int isRem1Rook = (last_valid_board[rem1_row][rem1_col] == 'R' ||
                          last_valid_board[rem1_row][rem1_col] == 'r');
        int isRem2Rook = (last_valid_board[rem2_row][rem2_col] == 'R' ||
                          last_valid_board[rem2_row][rem2_col] == 'r');

        if (isRem1King && isRem2Rook) {
            king_rem_index = 1;
            rook_rem_index = 2;
        } else if (isRem2King && isRem1Rook) {
            king_rem_index = 2;
            rook_rem_index = 1;
        } else {
            return 0;
        }

        int king_src_row = 0, king_src_col = 0, king_dst_row = 0, king_dst_col = 0;
        int validMapping = 0;
        for (int mapping = 0; mapping < 2; mapping++) {
            int temp_king_src_row, temp_king_src_col, temp_king_dst_row, temp_king_dst_col;
            int rook_src_row, rook_src_col, rook_dst_row, rook_dst_col;
            if (king_rem_index == 1) {
                temp_king_src_row = rem1_row; temp_king_src_col = rem1_col;
                rook_src_row = rem2_row; rook_src_col = rem2_col;
            } else {
                temp_king_src_row = rem2_row; temp_king_src_col = rem2_col;
                rook_src_row = rem1_row; rook_src_col = rem1_col;
            }
            if (mapping == 0) {
                temp_king_dst_row = add1_row; temp_king_dst_col = add1_col;
                rook_dst_row = add2_row; rook_dst_col = add2_col;
            } else {
                temp_king_dst_row = add2_row; temp_king_dst_col = add2_col;
                rook_dst_row = add1_row; rook_dst_col = add1_col;
            }
            if (temp_king_src_row != temp_king_dst_row)
                continue;
            if (abs(temp_king_dst_col - temp_king_src_col) != 2)
                continue;
            int expected_rook_dst_col;
            if (temp_king_dst_col > temp_king_src_col)
                expected_rook_dst_col = temp_king_dst_col - 1;
            else
                expected_rook_dst_col = temp_king_dst_col + 1;
            if (rook_src_row != temp_king_src_row)
                continue;
            if (rook_dst_row != temp_king_src_row)
                continue;
            if (rook_dst_col != expected_rook_dst_col)
                continue;
            king_src_row = temp_king_src_row;
            king_src_col = temp_king_src_col;
            king_dst_row = temp_king_dst_row;
            king_dst_col = temp_king_dst_col;
            validMapping = 1;
            break;
        }
        
        if (!validMapping)
            return 0;
        sprintf(current_move, "%c%d%c%d", 
            columns_names[king_src_col], king_src_row + 1, 
            columns_names[king_dst_col], king_dst_row + 1);
        return 1;
        
    }
    return 0;
}

void app_main(void)
{
    char whitePieces[] = {'R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'};
    char blackPieces[] = {'r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'};

    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            if (i == 0) { 
                last_valid_board[i][j] = whitePieces[j];
            } else if (i == 1) { 
                last_valid_board[i][j] = 'P';
            } else if (i == 6) { 
                last_valid_board[i][j] = 'p';
            } else if (i == 7) { 
                last_valid_board[i][j] = blackPieces[j];
            } else {
                last_valid_board[i][j] = '.';
            }
        }
    }
    int current_board[8][8] = {
        {1, 1, 1, 1, 1, 1, 1, 1},
        {1, 1, 1, 1, 1, 1, 1, 1},
        {0, 0, 0, 0, 0, 0, 0, 0},
        {0, 0, 0, 0, 0, 0, 0, 0},
        {0, 0, 0, 0, 0, 0, 0, 0},
        {0, 0, 0, 0, 0, 0, 0, 0}, 
        {1, 1, 1, 1, 1, 1, 1, 1}, 
        {1, 1, 1, 1, 1, 1, 1, 1}
    };
    setup_interrupt();
    int i = 0;
    int j = 0;
    gpio_num_t columns[] = {GPIO_NUM_15, GPIO_NUM_2, GPIO_NUM_4, GPIO_NUM_16, GPIO_NUM_17, GPIO_NUM_5, GPIO_NUM_18, GPIO_NUM_19};
    gpio_num_t rows[] = {GPIO_NUM_14, GPIO_NUM_27, GPIO_NUM_26, GPIO_NUM_25, GPIO_NUM_33, GPIO_NUM_32, GPIO_NUM_35, GPIO_NUM_34};
    char columns_names[] = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'};
    char addList[256];
    char removeList[256];
    int number_of_adds;
    int number_of_removes;
    char aux[3];
    ESP_ERROR_CHECK(i2c_master_init());
    lcd_init();
    uart_init_config();
    lcd_clear();
    lcd_set_cursor(0,0);
    lcd_write_string("Aguardando nova");
    lcd_set_cursor(3,1);
    lcd_write_string("partida...");
    xTaskCreate(uart_rx_task, "uart_rx_task", 4096, NULL, 10, NULL);
    while(1){
        clean_change_list(addList, 256);
        clean_change_list(removeList, 256);
        clean_change_list(aux, 3);
        int has_changed = 0;
        number_of_adds = 0;
        number_of_removes = 0;
        for(i = 0; i < 8; i++){
            gpio_set_level(columns[i], 1);
            for (j = 0; j < 8; j++){
                int leitura_estavel = gpio_get_level(rows[j]);
                vTaskDelay(10 / portTICK_PERIOD_MS);
                if (leitura_estavel == gpio_get_level(rows[j])) {
                    if (leitura_estavel == 1 && current_board[j][i] == 0) {
                        printf("Peça em %c%d\n", columns_names[i], j + 1);
                        current_board[j][i] = 1;
                        has_changed = 1;
                    }
                    else if (leitura_estavel == 0 && current_board[j][i] == 1) {
                        printf("Levantou em %c%d\n", columns_names[i], j + 1);
                        current_board[j][i] = 0;
                        has_changed = 1;
                    }
                    if (current_board[j][i] == 0 && last_valid_board[j][i] != '.'){
                        sprintf(aux, "%i%i", j, i); 
                        removeList[number_of_removes*2] = aux[0];
                        removeList[number_of_removes*2 + 1] = aux[1];
                        number_of_removes++;
                    }
                    else if (current_board[j][i] == 1 && last_valid_board[j][i] == '.'){
                        sprintf(aux, "%i%i", j, i); 
                        addList[number_of_adds*2] = aux[0];
                        addList[number_of_adds*2 + 1] = aux[1];
                        number_of_adds++;
                    }
                }
            }
            gpio_set_level(columns[i], 0);
        }
        if (number_of_adds + number_of_removes && has_changed){
            int valid = verify_valid_board(current_board, number_of_adds, number_of_removes, addList, removeList);
            if (valid){
                gpio_set_level(GPIO_NUM_12, 0);
                gpio_set_level(GPIO_NUM_13, 1);
                move_valid = true;
            }
            else{
                gpio_set_level(GPIO_NUM_12, 1);
                gpio_set_level(GPIO_NUM_13, 0);
                move_valid = false;
            }
            printf("Válido: %i | Adds: %i | Removes: %i\nRemove List: %s\nAdd List: %s\n", valid, number_of_adds, number_of_removes, removeList, addList);            
            print_board(current_board);
        }
        if (buttonPressed) {
            buttonPressed = false;
            if (move_valid) {
                printf("move: %s\n", current_move);
                int src_letter = current_move[0] - 'a';        // 'a' -> 0, 'b' -> 1, etc.
                int src_digit  = (current_move[1] - '0') - 1;    // '3' -> 3 - 1 = 2
                int dst_letter = current_move[2] - 'a';
                int dst_digit  = (current_move[3] - '0') - 1;            
                last_valid_board[dst_digit][dst_letter] = last_valid_board[src_digit][src_letter];
                last_valid_board[src_digit][src_letter] = '.';
                gpio_set_level(GPIO_NUM_12, 1);
                gpio_set_level(GPIO_NUM_13, 0);
                move_valid = false; 
                strcpy(last_move, current_move);
            }
        }
        vTaskDelay(10/portTICK_PERIOD_MS);
    }
}
