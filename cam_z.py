import board
import busio
import bitbangio
import time
import array

# --- НАСТРОЙКА I2C ДЛЯ OV7670 ---
i2c = busio.I2C(board.GP9, board.GP11) # SCL, SDA (подставьте свои)

def write_reg(reg, val):
    i2c.try_lock()
    i2c.writeto(0x21, bytes([reg, val]), stop=True)
    i2c.unlock()

def init_ov7670_grayscale_8mhz():
    # Сброс
    write_reg(0x12, 0x80)
    time.sleep(0.1)
    
    # Установка частоты 8 МГц (зависит от кварца на вашей плате OV7670, обычно 24MHz)
    # Формула сложная, это примерная настройка PLL
    write_reg(0x11, 0x01) # CLKRC: Prescaler
    write_reg(0x2A, 0x00) # DM_LN_H
    write_reg(0x2B, 0x05) # DM_LN_L
    write_reg(0x2C, 0x00) # DM_CN_H
    write_reg(0x2D, 0x04) # DM_CN_L
    write_reg(0x2E, 0x00) # DM_PPL_H
    write_reg(0x2F, 0x41) # DM_PPL_L
    
    # Режим VGA (640x480)
    write_reg(0x0C, 0x04) # COM3: Scale enable
    write_reg(0x12, 0x00) # COM7: VGA
    
    # Черно-белый режим (YUV, берем только канал Y)
    write_reg(0x40, 0xC0) # COM15: Output format RGB565 ->换成YUV
    write_reg(0x13, 0x88) # COM13: Убираем UV, только яркость (Grayscale)
    
    # Настройка окна (VGA)
    write_reg(0x17, 0x11) # HSTART
    write_reg(0x18, 0x61) # HSTOP
    write_reg(0x19, 0x03) # VSTART
    write_reg(0x1A, 0x9B) # VSTOP
    write_reg(0x32, 0x80) # HREF
    write_reg(0x03, 0x0A) # VREF

# --- ПОРТЫ ДЛЯ ПАРАЛЛЕЛЬНОГО ВВОДА ---
# ВНИМАНИЕ: bitbangio.ParallelIn работает медленно! 
# Для реальной работы потребуется писать асмовскую вставку для PIO.
pins = [board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP7]
pclk = board.GP8
href = board.GP9
vsync = board.GP10

parallel = bitbangio.ParallelIn(pins)

# --- ВАШИ БУФЕРЫ И УКАЗАТЕЛИ ---
BUFFER_SIZE = 640
LINES_PER_FRAME = 480

buf1 = bytearray(BUFFER_SIZE)
buf2 = bytearray(BUFFER_SIZE)

read_ptr = buf1   # Указатель для накопления
proc_ptr = buf2   # Указатель для обработки

# --- ЗАГЛУШКИ ДЛЯ ОБРАБОТКИ ---
def process_line(line_buffer, line_number):
    # Здесь ваша обработка строки
    pass

def process_frame():
    # Здесь обработка конца кадра
    pass

# --- ГЛАВНЫЙ ЦИКЛ ЗАХВАТА ---
def capture_loop():
    global read_ptr, proc_ptr
    
    init_ov7670_grayscale_8mhz()
    print("Камера инициализирована. Ожидание кадра...")
    
    # В чистом питоне мы вынуждены опрашивать пины в цикле
    vsync_pin = vsync
    href_pin = href
    pclk_pin = pclk
    
    while True:
        # 1. Ждем начала кадра (VSYNC = 0)
        while vsync_pin.value:
            pass
        while not vsync_pin.value:
            pass # Ждем пока VSYNC снова поднимется (начало активной области)
            
        # 2. Цикл по строкам
        for line_num in range(LINES_PER_FRAME):
            
            # Ждем начала строки (HREF = 1)
            while not href_pin.value:
                pass
                
            # Чтение 640 байт (ВНИМАНИЕ: на 8МГц тут будет мусор из-за скорости Python)
            byte_idx = 0
            while href_pin.value and byte_idx < BUFFER_SIZE:
                # Ждем спада PCLK
                while pclk_pin.value:
                    pass
                # Читаем данные
                read_ptr[byte_idx] = parallel.read()
                byte_idx += 1
                # Ждем поднятия PCLK (формируем полный период)
                while not pclk_pin.value:
                    pass

            # 3. Обмен указателей (Ping-Pong)
            read_ptr, proc_ptr = proc_ptr, read_ptr
            
            # 4. Вызов обработки строки
            process_line(proc_ptr, line_num)
            
            # Если VSYNC упал раньше времени - кадр битый, выходим
            if not vsync_pin.value:
                break
                
        # 5. Вызов обработки кадра
        process_frame()

# Запуск
capture_loop()
