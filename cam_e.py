import board
import busio
import digitalio
import pwmio
import time
import struct

# Настройка I2C для управления камерой
i2c = busio.I2C(board.GP0, board.GP1)

# Адрес OV7670 (SCCB)
OV7670_ADDR = 0x21

# Регистры OV7670 для VGA 640x480 и grayscale
REG_COM7 = 0x12
REG_COM3 = 0x0C
REG_COM14 = 0x3E
REG_HSTART = 0x17
REG_HSTOP = 0x18
REG_VSTART = 0x19
REG_VSTOP = 0x1A
REG_HREF = 0x32
REG_TSLB = 0x3A
REG_COM15 = 0x40
REG_SCALING_XSC = 0x70
REG_SCALING_YSC = 0x71
REG_SCALING_DCWCTR = 0x72
REG_SCALING_PCLK_DIV = 0x73
REG_SCALING_PCLK_DELAY = 0x74

# Инициализация камеры
def ov7670_init():
    # Сброс камеры
    i2c.writeto_mem(OV7670_ADDR, REG_COM7, b'\x80')
    time.sleep(0.1)
    
    # Настройка VGA 640x480
    i2c.writeto_mem(OV7670_ADDR, REG_HSTART, b'\x01')
    i2c.writeto_mem(OV7670_ADDR, REG_HSTOP, b'\x50')
    i2c.writeto_mem(OV7670_ADDR, REG_VSTART, b'\x03')
    i2c.writeto_mem(OV7670_ADDR, REG_VSTOP, b'\x33')
    i2c.writeto_mem(OV7670_ADDR, REG_HREF, b'\x00')
    
    # Настройка scaling
    i2c.writeto_mem(OV7670_ADDR, REG_SCALING_XSC, b'\x3A')
    i2c.writeto_mem(OV7670_ADDR, REG_SCALING_YSC, b'\x35')
    i2c.writeto_mem(OV7670_ADDR, REG_SCALING_DCWCTR, b'\x11')
    i2c.writeto_mem(OV7670_ADDR, REG_SCALING_PCLK_DIV, b'\x03')
    i2c.writeto_mem(OV7670_ADDR, REG_SCALING_PCLK_DELAY, b'\x02')
    
    # Настройка PLL и clock
    i2c.writeto_mem(OV7670_ADDR, REG_COM14, b'\x02')  # 2x clock scaling
    
    # Настройка output format (grayscale)
    i2c.writeto_mem(OV7670_ADDR, REG_TSLB, b'\x04')   # YUYV format (for grayscale extraction)
    i2c.writeto_mem(OV7670_ADDR, REG_COM15, b'\x00')  # RGB format (will extract Y)
    
    # Активация VGA mode
    i2c.writeto_mem(OV7670_ADDR, REG_COM7, b'\x00')  # Clear reset bit

# Настройка тактирования 8 MHz
def setup_clock():
    # Используем PWM для генерации MCLK (GP2)
    clock_pin = board.GP2
    pwm = pwmio.PWMOut(clock_pin, frequency=8_000_000, duty_cycle=0x8000)
    return pwm

# Настройка пинов камеры
def setup_camera_pins():
    # VSYNC (GP3) и HREF (GP4) как входы
    vsync = digitalio.DigitalInOut(board.GP3)
    vsync.direction = digitalio.Direction.INPUT
    vsync.pull = digitalio.Pull.UP
    
    href = digitalio.DigitalInOut(board.GP4)
    href.direction = digitalio.Direction.INPUT
    href.pull = digitalio.Pull.UP
    
    # D0-D7 (GP5-GP12) как входы
    data_pins = [board.GP5, board.GP6, board.GP7, board.GP8,
                 board.GP9, board.GP10, board.GP11, board.GP12]
    data_inputs = [digitalio.DigitalInOut(pin) for pin in data_pins]
    for pin in data_inputs:
        pin.direction = digitalio.Direction.INPUT
        pin.pull = digitalio.Pull.UP
    
    return vsync, href, data_inputs

# Буферы и указатели
buffer0 = bytearray(640)
buffer1 = bytearray(640)
write_buffer = buffer0
read_buffer = buffer1
write_index = 0
line_count = 0

# Флаги состояния
frame_ready = False
line_ready = False

# Обработчик VSYNC (начало кадра)
def vsync_handler(pin):
    global line_count, write_index, write_buffer, read_buffer
    if not pin.value:  # Falling edge
        line_count = 0
        write_index = 0
        # Сброс буферов
        write_buffer = buffer0
        read_buffer = buffer1
        frame_ready = False

# Обработчик HREF (начало строки)
def href_handler(pin):
    global write_index
    if pin.value:  # Rising edge
        write_index = 0

# Чтение данных строки
def read_line(data_inputs):
    global write_index
    for i in range(640):
        # Чтение 8 бит (D0-D7)
        byte_val = 0
        for j, pin in enumerate(data_inputs):
            byte_val |= pin.value << j
        write_buffer[write_index] = byte_val
        write_index += 1

# Основные процедуры обработки
def process_line(line_data):
    # Здесь обработка одной строки (640 байт)
    pass  # Заглушка

def process_frame():
    # Здесь обработка полного кадра
    pass  # Заглушка

# Инициализация
ov7670_init()
pwm = setup_clock()
vsync, href, data_inputs = setup_camera_pins()

# Настройка прерываний
vsync.irq(trigger=digitalio.Edge.FALL, handler=vsync_handler)
href.irq(trigger=digitalio.Edge.RISING, handler=href_handler)

# Основной цикл
while True:
    if line_ready:
        # Меняем буферы местами
        write_buffer, read_buffer = read_buffer, write_buffer
        process_line(read_buffer)
        line_ready = False
        line_count += 1
        
        if line_count >= 480:
            process_frame()
            line_count = 0
            frame_ready = True
    
    # Чтение данных при активном HREF
    if href.value:
        read_line(data_inputs)
        if write_index >= 640:
            line_ready = True
