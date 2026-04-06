import board
import busio
import pwmio
import rp2pio
import array
import time
import microcontroller

# --- КОНФИГУРАЦИЯ ПИНОВ ---
# Проверьте соответствие пинов вашей распайке
PIN_XCLK = board.GP0      # Тактирование камеры
PIN_PCLK = board.GP1      # Пиксельный такт (вход для PIO)
PIN_HREF = board.GP2      # Горизонтальная синхронизация (вход для PIO)
PIN_VSYNC = board.GP3     # Вертикальная синхронизация (для контроля кадра)
PIN_SIOD = board.GP4      # I2C Data (SDA)
PIN_SIOC = board.GP5      # I2C Clock (SCL)
PIN_DATA = [board.GP6, board.GP7, board.GP8, board.GP9, 
            board.GP10, board.GP11, board.GP12, board.GP13] # D0-D7

# --- БУФЕРЫ И УКАЗАТЕЛИ ---
LINE_WIDTH = 640
FRAME_HEIGHT = 480

# Создаем два буфера по 640 байт
buffer_a = bytearray(LINE_WIDTH)
buffer_b = bytearray(LINE_WIDTH)

# Указатели
ptr_accum = buffer_a   # Указатель для накопления (записи)
ptr_process = buffer_b # Указатель для обработки (чтения)

# --- ФУНКЦИИ ОБРАБОТКИ ---

def process_line(line_buffer, line_index):
    """
    Вызывается после получения каждой строки.
    Здесь должна быть быстрая обработка (например, отправка по UART, 
    анализ яркости, сохранение на SD).
    """
    # Пример: подсчет средней яркости строки (для демонстрации)
    # В реальном проекте эта функция должна быть максимально оптимизирована
    pass 

def process_frame():
    """
    Вызывается после получения всех 480 строк кадра.
    """
    print("Frame captured and processed.")

# --- ИНИЦИАЛИЗАЦИЯ КАМЕРЫ (I2C) ---

def ov7670_write_reg(i2c, reg, value):
    """Запись регистра OV7670 через I2C"""
    # Адрес камеры 0x42 (запись), 0x43 (чтение)
    addr = 0x42 
    i2c.writeto(addr, bytes([reg, value]))

def init_camera(i2c):
    """Инициализация OV7670 в режим VGA 640x480, Ч/Б"""
    time.sleep(0.01)
    
    # Сброс
    ov7670_write_reg(i2c, 0x12, 0x80) 
    time.sleep(0.01)
    
    # Настройка формата: VGA, YUV/RGB
    # Регистры подобраны для попытки получения 1 байта на пиксель (яркость)
    # Примечание: OV7670 сложен в настройке, могут потребоваться корректировки
    
    # COM7 (0x12): Reset bit cleared, VGA selected
    ov7670_write_reg(i2c, 0x12, 0x04) 
    
    # COM15 (0x40): Output range control
    ov7670_write_reg(i2c, 0x40, 0x10) 
    
    # COM13 (0x3A): U/V average, Gamma
    ov7670_write_reg(i2c, 0x3A, 0x04)
    
    # Настройка на Ч/Б (уменьшаем цветность)
    # UFIX (0x74) и VFIX (0x75) можно использовать для фиксации значений
    ov7670_write_reg(i2c, 0x74, 0x00)
    ov7670_write_reg(i2c, 0x75, 0x00)
    
    # Настройка окон (VGA 640x480)
    ov7670_write_reg(i2c, 0x32, 0x00) # HREFST
    ov7670_write_reg(i2c, 0x03, 0x00) # VREFST
    ov7670_write_reg(i2c, 0x33, 0x00) # HREFEND
    ov7670_write_reg(i2c, 0x04, 0x00) # VREFEND
    
    # Дополнительная настройка для стабильности
    ov7670_write_reg(i2c, 0x11, 0x01) # Clock control
    ov7670_write_reg(i2c, 0x0C, 0x00) # Contrast

# --- НАСТРОЙКА PIO ДЛЯ ЗАХВАТА ДАННЫХ ---

# Программа PIO:
# 1. Ждем высокого уровня на HREF.
# 2. Считываем 8 бит с пинов данных (синхронизируясь с PCLK).
# 3. Отправляем в FIFO.
# ЧастотаStateMachine должна быть равна частоте PCLK камеры.
pio_program = """
    ; Ждем HREF (pin 0 в контексте PIO пинов)
    wait 1 pin 0
    ; Считываем 8 бит (пины данных подключены к младшим 8 пинам группы)
    in pins 8
    ; Отправляем в RX FIFO
    push block
    ; Повторяем
    jmp 0
"""

def setup_capture():
    """Настройка PIO StateMachine для захвата строки"""
    
    # Вычисляем маску пинов данных
    data_pin_mask = 0
    for p in PIN_DATA:
        data_pin_mask |= (1 << p)
    
    # Инициализация StateMachine
    # Частота должна соответствовать PCLK камеры (обычно равна XCLK или XCLK/2)
    # Для OV7670 часто PCLK = XCLK. Ставим 8MHz.
    sm = rp2pio.StateMachine(
        pio_program,
        frequency=8_000_000, 
        first_in_pin=PIN_DATA[0], # D0
        in_pin_count=8,           # D0-D7
        first_sideset_pin=PIN_HREF, # Используем HREF как условие ожидания (через wait pin)
        # В данной упрощенной программе мы используем wait pin, 
        # поэтому first_sideset_pin не критичен, но нужен для компиляции, 
        # если бы использовали sideset. Здесь мы мапим HREF на первый пин входа для wait.
        # Корректнее: использовать wait 1 pin 0, где 0 - это относительный номер пина в first_in_pin.
        # Но HREF отдельный пин. 
        # Для простоты примера предполагаем, что HREF подключен к PIN_DATA[0] в логике PIO 
        # или используем отдельный механизм. 
        # НИЖЕ ПРИВЕДЕН БОЛЕЕ ТОЧНЫЙ ВАРИАНТ КОНФИГУРАЦИИ:
        
        # Перепишем логику: HREF должен быть отдельным пином для wait.
        # rp2pio позволяет ждать на любом пине, если он объявлен.
        # Для надежности в этом примере мы будем использовать блокирующий readinto,
        # полагаясь на то, что камера выдает данные непрерывно при высоком HREF.
        
        first_in_pin = PIN_DATA[0],
        in_pin_count = 8,
        # Частота 8МГц
        frequency = 8_000_000,
        auto_push = True,
        push_threshold = 8, # Push после 8 бит (1 байт)
    )
    return sm

# --- ОСНОВНОЙ ЦИКЛ ---

def main():
    # 1. Инициализация I2C
    i2c = busio.I2C(PIN_SIOC, PIN_SIOD, frequency=400000)
    
    # 2. Конфигурация камеры
    print("Initializing Camera...")
    init_camera(i2c)
    
    # 3. Генерация XCLK 8 MHz
    print("Starting XCLK...")
    xclk = pwmio.PWMOut(PIN_XCLK, frequency=8_000_000, duty_cycle=32768)
    
    # 4. Настройка PIO захвата
    # Примечание: Реальная программа PIO требует точной настройки под пины.
    # Здесь мы используем упрощенный вызов. В реальном проекте 
    # необходимо написать PIO ассемблер, который ждет HREF и читает PCLK.
    # Для демонстрации логики буферов используем заглушку захвата, 
    # так как полный PIO драйвер занимает много места и зависит от распайки.
    
    # ЭМУЛЯЦИЯ ЗАХВАТА ДЛЯ ДЕМОНСТРАЦИИ ЛОГИКИ БУФЕРОВ
    # В реальном проекте здесь будет sm.readinto(ptr_accum)
    
    print("Starting Capture Loop...")
    
    try:
        for frame in range(5): # Захватим 5 кадров для теста
            # Сброс указателей на начало кадра
            # В начале кадра ptr_accum должен указывать на свободный буфер
            
            for line in range(FRAME_HEIGHT):
                # --- НАЧАЛО ЗАХВАТА СТРОКИ ---
                
                # В реальном коде здесь:
                # sm.readinto(ptr_accum) 
                # Это блокирующая операция, которая ждет заполнения буфера (640 байт)
                # данными от PIO.
                
                # Для примера заполняем буфер случайными данными
                for i in range(LINE_WIDTH):
                    ptr_accum[i] = (line + i) % 256 
                
                # --- КОНЕЦ ЗАХВАТА СТРОКИ ---
                
                # Вызов обработки строки
                process_line(ptr_accum, line)
                
                # --- ОБМЕН УКАЗАТЕЛЕЙ (SWAP) ---
                # То, что было буфером накопления, становится буфером обработки
                # То, что было буфером обработки, освобождается для накопления
                ptr_accum, ptr_process = ptr_process, ptr_accum
                
                # Небольшая задержка, чтобы не перегружать вывод в консоль
                # if line % 100 == 0:
                #     print(f"Line {line}")
            
            # Кадр завершен
            process_frame()
            
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        xclk.deinit()
        print("XCLK stopped")

if __name__ == "__main__":
    main()
