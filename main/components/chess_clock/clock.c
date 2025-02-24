#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#include "driver/i2c.h"
#include "esp_log.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>

extern void esp_rom_delay_us(uint32_t us);


// Configurações da UART
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

// Função para atualizar o display com os tempos recebidos
void update_lcd_clock(const char *msg) {
    char msg_winner[64];
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
        return;
    }
    // Espera-se o formato: "white_time;last_move;black_time"
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
            char last_move[10];
            strncpy(last_move, token, sizeof(last_move)-1);
            last_move[sizeof(last_move)-1] = '\0';
            
            token = strtok(NULL, ";");
            if (token != NULL) {
                char black_time[10];
                strncpy(black_time, token, sizeof(black_time)-1);
                black_time[sizeof(black_time)-1] = '\0';
                
                snprintf(header, sizeof(header), "WHITE  LM  BLACK");  // Cabeçalho fixo (16 caracteres)
                snprintf(line2, sizeof(line2), "%5.5s %-3.3s  %5.5s", white_time, last_move, black_time);

                
                lcd_clear();
                lcd_set_cursor(0,0);
                lcd_write_string(header);
                lcd_set_cursor(0,1);
                lcd_write_string(line2);
                return;
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

void app_main(void)
{
    ESP_ERROR_CHECK(i2c_master_init());
    lcd_init();
    
    uart_init_config();
    xTaskCreate(uart_rx_task, "uart_rx_task", 4096, NULL, 10, NULL);
    
    // Exibe mensagem inicial
    lcd_clear();
    lcd_set_cursor(0,0);
    lcd_write_string("Aguardando nova");
    lcd_set_cursor(3,1);
    lcd_write_string("partida...");
    
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}