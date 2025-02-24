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
#define BUTTON_PIN GPIO_NUM_23
volatile bool buttonPressed = false;
bool move_valid = false;              
char last_move[10];         
#define BOARD_SIZE 8
#define entrada  ((1ULL << 14) | (1ULL << 25) | (1ULL << 26) | (1ULL << 27) | (1ULL << 32) | (1ULL << 33) | (1ULL << 34) | (1ULL << 35))
#define saidas  ((1ULL << 15) | (1ULL << 2) | (1ULL << 4) | (1ULL << 16) | (1ULL << 17) | (1ULL << 5) | (1ULL << 18) | (1ULL << 19) | (1ULL << 12) | (1ULL << 13))


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
                  int current_board[BOARD_SIZE][BOARD_SIZE], char last_valid_board[BOARD_SIZE][BOARD_SIZE]) {
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

int verify_valid_board(int current_board[8][8], char last_valid_board[8][8], int num_adds, int number_of_removes, char addList[], char removeList[]){
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
    
        if (!is_valid_move(piece, src_row, src_col, dst_row, dst_col, current_board, last_valid_board))
            return 0;
        if ((piece == 'p') && src_row == 6 && dst_row == 7){
            sprintf(last_move, "%c%d%c%d", 
                columns_names[src_col], src_row + 1, 
                columns_names[dst_col], dst_row + 1);
        }
        else if ((piece == 'P') && src_row == 1 && dst_row == 0){
            sprintf(last_move, "%c%d%c%d", 
                columns_names[src_col], src_row + 1, 
                columns_names[dst_col], dst_row + 1);
        }
        else{
        sprintf(last_move, "%c%d%c%d", 
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
        sprintf(last_move, "%c%d%c%d", 
            columns_names[king_src_col], king_src_row + 1, 
            columns_names[king_dst_col], king_dst_row + 1);
        return 1;
        
    }
    return 0;
}

void app_main(void)
{
    char last_valid_board[8][8];
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
    current_board[7][0] = 0;
    last_valid_board[7][0] = '.';
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
            int valid = verify_valid_board(current_board, last_valid_board, number_of_adds, number_of_removes, addList, removeList);
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
                printf("move: %s\n", last_move);
                int src_letter = last_move[0] - 'a';        // 'a' -> 0, 'b' -> 1, etc.
                int src_digit  = (last_move[1] - '0') - 1;    // '3' -> 3 - 1 = 2
                int dst_letter = last_move[2] - 'a';
                int dst_digit  = (last_move[3] - '0') - 1;            
                last_valid_board[dst_digit][dst_letter] = last_valid_board[src_digit][src_letter];
                last_valid_board[src_digit][src_letter] = '.';
                gpio_set_level(GPIO_NUM_12, 1);
                gpio_set_level(GPIO_NUM_13, 0);
                move_valid = false; 
            }
        }
        vTaskDelay(10/portTICK_PERIOD_MS);
    }
}
