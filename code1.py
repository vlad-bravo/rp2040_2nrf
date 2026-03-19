import board
import busio
import digitalio
import neopixel
import time

# --- Константы регистров nRF24L01 ---
# Регистры конфигурации
REG_CONFIG       = 0x00
REG_EN_AA        = 0x01
REG_EN_RXADDR    = 0x02
REG_SETUP_AW     = 0x03
REG_SETUP_RETR   = 0x04
REG_RF_CH        = 0x05
REG_RF_SETUP     = 0x06
REG_STATUS       = 0x07
REG_RX_ADDR_P0   = 0x0A
REG_RX_ADDR_P1   = 0x0B
REG_TX_ADDR      = 0x10
REG_DYNPD        = 0x1C
REG_FEATURE      = 0x1D

# Команды
CMD_R_REGISTER    = 0x00
CMD_W_REGISTER    = 0x20
CMD_W_TX_PAYLOAD  = 0xA0
CMD_R_RX_PAYLOAD  = 0x61
CMD_FLUSH_TX      = 0xE1
CMD_FLUSH_RX      = 0xE2
CMD_W_ACK_PAYLOAD = 0xA8

# Биты
MASK_RX_DR       = (1 << 6)
MASK_TX_DS       = (1 << 5)
MASK_MAX_RT      = (1 << 4)
MASK_PWR_UP      = (1 << 1)
MASK_PRIM_RX     = (1 << 0)

# --- Настройка Neopixel ---
pixel = neopixel.NeoPixel(board.GP23, 1, brightness=0.3)

def set_color(r, g, b):
    pixel[0] = (r, g, b)

# --- Класс драйвера nRF24L01 ---
class NRF24L01:
    def __init__(self, spi, csn_pin, ce_pin):
        self.spi = spi
        self.csn = csn_pin
        self.ce = ce_pin
        
        # Настройка пинов
        self.csn.direction = digitalio.Direction.OUTPUT
        self.ce.direction = digitalio.Direction.OUTPUT
        
        self.csn.value = True  # CSN High (неактивен)
        self.ce.value = False  # CE Low (Standby)

    def reg_write(self, reg, value):
        """Запись одного байта в регистр"""
        self.csn.value = False
        self.spi.write(bytes([CMD_W_REGISTER | reg, value]))
        self.csn.value = True

    def reg_read(self, reg):
        """Чтение одного байта из регистра"""
        self.csn.value = False
        self.spi.write(bytes([CMD_R_REGISTER | reg]))
        result = bytearray(1)
        self.spi.readinto(result)
        self.csn.value = True
        return result[0]

    def write_addr(self, reg, addr):
        """Запись адреса (5 байт)"""
        self.csn.value = False
        self.spi.write(bytes([CMD_W_REGISTER | reg]))
        self.spi.write(addr)
        self.csn.value = True

    def write_payload(self, data, ack_payload=False, pipe=0):
        """Запись данных в буфер"""
        self.csn.value = False
        if ack_payload:
            # Формула для W_ACK_PAYLOAD: 0xA8 | pipe_number
            self.spi.write(bytes([CMD_W_ACK_PAYLOAD | pipe]))
        else:
            self.spi.write(bytes([CMD_W_TX_PAYLOAD]))
        self.spi.write(data)
        self.csn.value = True

    def read_payload(self, length):
        """Чтение данных из буфера"""
        self.csn.value = False
        self.spi.write(bytes([CMD_R_RX_PAYLOAD]))
        data = bytearray(length)
        self.spi.readinto(data)
        self.csn.value = True
        return data

    def flush_tx(self):
        self.csn.value = False
        self.spi.write(bytes([CMD_FLUSH_TX]))
        self.csn.value = True

    def flush_rx(self):
        self.csn.value = False
        self.spi.write(bytes([CMD_FLUSH_RX]))
        self.csn.value = True

    def power_up_rx(self):
        """Перевод в режим приема"""
        self.reg_write(REG_CONFIG, self.reg_read(REG_CONFIG) | MASK_PWR_UP | MASK_PRIM_RX)
        self.ce.value = True
        time.sleep(0.001) # 1.5ms settling

    def power_up_tx(self):
        """Перевод в режим передачи"""
        self.reg_write(REG_CONFIG, (self.reg_read(REG_CONFIG) | MASK_PWR_UP) & ~MASK_PRIM_RX)
        # CE дергается при отправке

    def clear_interrupts(self):
        """Сброс флагов прерываний"""
        self.reg_write(REG_STATUS, MASK_RX_DR | MASK_TX_DS | MASK_MAX_RT)

# --- Инициализация устройств ---

# Устройство 0 (TX) - SPI0
spi0 = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)
while not spi0.try_lock():
    pass
spi0.configure(baudrate=4000000, phase=0, polarity=0)
# CS (Chip Enable) -> CE, CSN -> CSN
nrf0 = NRF24L01(spi0, csn_pin=board.GP8, ce_pin=board.GP13)

# Устройство 1 (RX) - SPI1
spi1 = busio.SPI(clock=board.GP2, MOSI=board.GP3, MISO=board.GP4)
while not spi1.try_lock():
    pass
spi1.configure(baudrate=4000000, phase=0, polarity=0)
nrf1 = NRF24L01(spi1, csn_pin=board.GP6, ce_pin=board.GP5)

# Общий адрес (5 байт)
ADDR = b'\xE7\xE7\xE7\xE7\xE7'

def setup_tx():
    """Настройка передатчика (nrf0)"""
    set_color(50, 50, 0) # Желтый - настройка
    nrf0.reg_write(REG_RF_CH, 76) # Канал
    nrf0.reg_write(REG_RF_SETUP, 0x06) # 1Mbps, 0dBm
    
    # Включаем Auto Ack на Pipe 0 (для приема ACK)
    nrf0.reg_write(REG_EN_AA, 0x01) 
    # Включаем приемник на Pipe 0 (для ACK)
    nrf0.reg_write(REG_EN_RXADDR, 0x01)
    
    # Включаем Dynamic Payload Length (DPL) на Pipe 0
    nrf0.reg_write(REG_DYNPD, 0x01)
    
    # Включаем фичи: DPL и Payload with ACK
    # Важно: порядок записи битов важен, если регистр сброшен.
    # Бит 2: EN_DPL, Бит 1: EN_ACK_PAY
    nrf0.reg_write(REG_FEATURE, 0x06) 
    
    # Устанавливаем адреса
    # TX адрес
    nrf0.write_addr(REG_TX_ADDR, ADDR)
    # RX адрес на Pipe 0 должен совпадать с TX адресом для приема ACK
    nrf0.write_addr(REG_RX_ADDR_P0, ADDR)
    
    # Очистка буферов
    nrf0.flush_tx()
    nrf0.flush_rx()
    nrf0.clear_interrupts()
    
    # Режим TX
    nrf0.power_up_tx()
    print("TX Ready")

def setup_rx():
    """Настройка приемника (nrf1)"""
    set_color(0, 50, 50) # Голубой - настройка
    nrf1.reg_write(REG_RF_CH, 76)
    nrf1.reg_write(REG_RF_SETUP, 0x06)
    
    # Auto Ack на Pipe 1
    nrf1.reg_write(REG_EN_AA, 0x02)
    # Включаем приемник на Pipe 1
    nrf1.reg_write(REG_EN_RXADDR, 0x02)
    
    # DPL на Pipe 1
    nrf1.reg_write(REG_DYNPD, 0x02)
    
    # Фичи DPL и ACK Payload
    nrf1.reg_write(REG_FEATURE, 0x06)
    
    # Слушаем на Pipe 1 по адресу ADDR
    nrf1.write_addr(REG_RX_ADDR_P1, ADDR)
    
    nrf1.flush_tx()
    nrf1.flush_rx()
    nrf1.clear_interrupts()
    
    # Режим RX (CE High)
    nrf1.power_up_rx()
    print("RX Ready")

# --- Основной цикл ---

setup_rx() # Сначала настраиваем RX
setup_tx() # Потом TX

counter = 0

while True:
    # 1. На RX (nrf1) загружаем данные для ответа
    # Эти данные улетят автоматически при получении пакета от TX
    ack_msg = bytes([0xF0, counter % 256]) # Заготовленный payload
    nrf1.write_payload(ack_msg, ack_payload=True, pipe=1)
    # Не забываем сбросить прерывания на RX, если были
    nrf1.clear_interrupts()
    
    # 2. На TX (nrf0) отправляем пакет
    tx_msg = bytes([0xA0, counter % 256])
    
    # Очищаем старые флаги
    nrf0.clear_interrupts()
    nrf0.flush_tx()
    
    # Пишем в буфер
    nrf0.write_payload(tx_msg)
    
    # Пульс CE для отправки
    nrf0.ce.value = True
    time.sleep(0.00001) # 10 мкс
    nrf0.ce.value = False
    
    set_color(100, 100, 0) # Желтый ярче - отправка
    print(f"TX Sending: {list(tx_msg)}")
    
    # 3. Ждем результата на TX
    start = time.monotonic()
    status = 0
    success = False
    
    while time.monotonic() - start < 0.1: # Таймаут 100мс
        status = nrf0.reg_read(REG_STATUS)
        if status & MASK_TX_DS: # Успешная отправка
            success = True
            break
        if status & MASK_MAX_RT: # Не доставлено (ретраисчерпаны)
            break
        time.sleep(0.001)
            
    if success:
        # Проверяем, пришел ли ACK Payload
        if status & MASK_RX_DR:
            # Читаем длину принятого пакета (через регистр R_RX_PL_WID, но мы используем фиксированную для простоты или читаем 32 байта)
            # В DPL нужно читать команду 0x60 (R_RX_PL_WID), но для упрощения прочтем 2 байта
            set_color(0, 255, 0) # Зеленый - успех + данные
            rx_data = nrf0.read_payload(2)
            print(f"TX Success! Got Ack Payload: {list(rx_data)}")
        else:
            set_color(0, 100, 0) # Темно-зеленый - успех, но пустой ACK
            print("TX Success (Empty ACK)")
            
        nrf0.flush_rx() # Очищаем RX буфер после чтения
    else:
        set_color(255, 0, 0) # Красный - ошибка
        print("TX Failed (Max RT)")
        nrf0.flush_tx()
        
    counter += 1
    time.sleep(1) # Пауза между циклами
