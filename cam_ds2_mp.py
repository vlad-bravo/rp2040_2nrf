from machine import Pin, I2C, PWM
import time

# === Конфигурация пинов ===
PINS = {
    'D0': 0, 'D1': 1, 'D2': 16, 'D3': 17,
    'D4': 18, 'D5': 19, 'D6': 20, 'D7': 21,
    'PCLK': 27, 'VSYNC': 23, 'HREF': 28, 'MCLK': 26
}

# === Регистры OV7670 ===
REG_GAIN = 0x00
REG_BLUE = 0x01
REG_RED = 0x02
REG_VREF = 0x03
REG_COM1 = 0x04
REG_BAVE = 0x05
REG_GEAVE = 0x06
REG_AECHH = 0x07
REG_RAVE = 0x08
REG_COM2 = 0x09
REG_PID = 0x0A
REG_VER = 0x0B
REG_COM3 = 0x0C
REG_COM4 = 0x0D
REG_COM5 = 0x0E
REG_COM6 = 0x0F
REG_AEC = 0x10
REG_CLKRC = 0x11
REG_COM7 = 0x12
REG_COM8 = 0x13
REG_COM9 = 0x14
REG_COM10 = 0x15
REG_HSTART = 0x17
REG_HSTOP = 0x18
REG_VSTART = 0x19
REG_VSTOP = 0x1A
REG_PSHFT = 0x1B
REG_MIDH = 0x1C
REG_MIDL = 0x1D
REG_MVFP = 0x1E
REG_AEW = 0x24
REG_AEB = 0x25
REG_VV = 0x26
REG_REG76 = 0x76
REG_COM11 = 0x3B
REG_COM12 = 0x3C
REG_COM13 = 0x3D
REG_COM14 = 0x3E
REG_COM15 = 0x3F
REG_COM16 = 0x40
REG_TSLB = 0x3A

# === Инициализация пинов ===
def init_pins():
    """Инициализация всех GPIO пинов"""
    # Пины данных (вход)
    for i in range(8):
        pin_num = PINS[f'D{i}']
        PINS[f'D{i}_dio'] = Pin(pin_num, Pin.IN)
    
    # Управляющие пины
    PINS['PCLK_dio'] = Pin(PINS['PCLK'], Pin.IN)
    PINS['VSYNC_dio'] = Pin(PINS['VSYNC'], Pin.IN)
    PINS['HREF_dio'] = Pin(PINS['HREF'], Pin.IN)
    
    # MCLK - используем PWM для генерации тактовой частоты
    # duty 32768 = 50% (из диапазона 0-65535)
    PINS['MCLK_pwm'] = PWM(PINS['MCLK'])
    PINS['MCLK_pwm'].freq(60_000_000)
    PINS['MCLK_pwm'].duty_u16(32768)

# === I2C коммуникация ===
def write_reg(i2c, reg, value):
    """Запись в регистр OV7670"""
    i2c.writeto(0x21, bytes([reg, value]))

def read_reg(i2c, reg):
    """Чтение регистра OV7670"""
    data = i2c.readfrom_mem(0x21, reg, 1)
    return data[0]

# === Настройка режимов камеры ===
def reset_camera(i2c):
    """Сброс камеры в известное состояние"""
    # Программный сброс через регистр COM7
    write_reg(i2c, REG_COM7, 0x80)
    time.sleep(0.1)

def init_ov7670(i2c):
    """Инициализация OV7670 для режима 640x480 YUV"""
    
    # Сброс камеры
    reset_camera(i2c)
    
    # Настройка тактового делителя (CLKRC)
    write_reg(i2c, REG_CLKRC, 0x00)
    
    # COM7: RGB | Resolution VGA | без сброса
    write_reg(i2c, REG_COM7, 0x06)
    
    # COM3: Включить масштабирование
    write_reg(i2c, REG_COM3, 0x04)
    
    # COM4: Без масштабирования
    write_reg(i2c, REG_COM4, 0x00)
    
    # COM5: Настройки AGC/AEC
    write_reg(i2c, REG_COM5, 0x61)
    
    # COM6: Настройки AGC
    write_reg(i2c, REG_COM6, 0x4B)
    
    # COM8: Включить AGC и AEC
    write_reg(i2c, REG_COM8, 0xE7)
    
    # COM9: Gain ceiling
    write_reg(i2c, REG_COM9, 0x4A)
    
    # COM10: PCLK output polarity
    write_reg(i2c, REG_COM10, 0x00)
    
    # COM11: ночной режим, PCLK инвертировать
    write_reg(i2c, REG_COM11, 0x02)
    
    # COM12: HREF polarity
    write_reg(i2c, REG_COM12, 0x08)
    
    # COM13: формат данных RGB/YUV
    write_reg(i2c, REG_COM13, 0x18)
    
    # COM14: Enable YUV output
    write_reg(i2c, REG_COM14, 0x18)
    
    # COM15: Выходной формат: YUYV
    write_reg(i2c, REG_COM15, 0xC0)
    
    # COM16: Замена U и V
    write_reg(i2c, REG_COM16, 0x00)
    
    # TSLB: Порядок байтов в YUV
    write_reg(i2c, REG_TSLB, 0x00)
    
    # Настройка окон (HSTART, HSTOP, VSTART, VSTOP для VGA)
    write_reg(i2c, REG_HSTART, 0x16)
    write_reg(i2c, REG_HSTOP, 0x76)
    write_reg(i2c, REG_VSTART, 0x02)
    write_reg(i2c, REG_VSTOP, 0x7A)
    
    # AGC/AEC настройки
    write_reg(i2c, REG_AECHH, 0x00)
    write_reg(i2c, REG_AEW, 0x64)
    write_reg(i2c, REG_AEB, 0x64)
    
    # Экспозиция
    write_reg(i2c, REG_VV, 0x00)
    write_reg(i2c, REG_REG76, 0x01)
    
    # Усиление и баланс белого
    write_reg(i2c, REG_GAIN, 0x00)
    write_reg(i2c, REG_BLUE, 0x80)
    write_reg(i2c, REG_RED, 0x80)
    
    # Включить автоматические настройки
    write_reg(i2c, REG_COM8, 0xE7)
    
    print("OV7670 инициализирована в режиме VGA YUV")
    pid = read_reg(i2c, REG_PID)
    ver = read_reg(i2c, REG_VER)
    print(f"ID камеры: 0x{pid:02X}{ver:02X}")

# === Захват строки ===
def capture_line(pclk, href, data_pins):
    """Захват одной строки 640 байт (только Y компонента)"""
    line_buffer = bytearray(640)
    pixel_index = 0
    
    # Ждем начала строки (HREF = HIGH)
    while not href.value():
        pass
    
    # Захватываем 640 пикселей (640 байт Y)
    while pixel_index < 640:
        # Ждем перепада PCLK
        last_pclk = pclk.value()
        while pclk.value() == last_pclk:
            pass
        
        # Читаем данные с шины
        data = 0
        for i in range(8):
            if data_pins[i].value():
                data |= (1 << i)
        
        # Берем только первый байт (Y) из каждого 16-битного слова YUYV
        if pixel_index % 2 == 0:
            line_buffer[pixel_index // 2] = data
        
        pixel_index += 1
    
    return line_buffer

# === Захват полного кадра ===
def capture_frame(width, height, process_line_cb):
    """Захват полного кадра с построчной обработкой"""
    
    # Два буфера по 640 байт
    buffer1 = bytearray(width)
    buffer2 = bytearray(width)
    
    fill_buffer = buffer1
    process_buffer = buffer2
    
    # Получаем объекты пинов
    vsync_pin = PINS['VSYNC_dio']
    href_pin = PINS['HREF_dio']
    pclk_pin = PINS['PCLK_dio']
    data_pins = [PINS[f'D{i}_dio'] for i in range(8)]
    
    row_count = 0
    
    # Ждем начала кадра (VSYNC = HIGH)
    while not vsync_pin.value():
        pass
    
    # Ждем VSYNC = LOW (начало активной области)
    while vsync_pin.value():
        pass
    
    # Захватываем все строки
    while row_count < height:
        # Ждем начала строки
        while not href_pin.value():
            if vsync_pin.value():
                break
        
        # Захватываем строку
        captured_line = capture_line(pclk_pin, href_pin, data_pins)
        
        # Копируем в активный буфер
        fill_buffer[:] = captured_line
        
        # Меняем указатели местами
        fill_buffer, process_buffer = process_buffer, fill_buffer
        
        # Обрабатываем предыдущую строку
        if row_count > 0:
            process_line_cb(row_count - 1, process_buffer)
        
        row_count += 1
    
    # Обрабатываем последнюю строку
    process_line_cb(row_count - 1, fill_buffer)
    
    return row_count

# === Процедуры обработки ===
def process_line(row_number, line_data):
    """Обработка одной строки"""
    if line_data:
        avg_brightness = sum(line_data) / len(line_data)
        if row_number % 50 == 0:
            print(f"Строка {row_number:3d}: средняя яркость = {avg_brightness:.1f}")

def process_frame():
    """Обработка полного кадра"""
    print("=== Кадр полностью получен и обработан ===")

# === Основная функция ===
def main():
    print("Инициализация пинов...")
    init_pins()
    
    # Инициализация I2C (GP1 = SDA, GP0 = SCL)
    i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400_000)
    
    # Поиск камеры на I2C шине
    devices = i2c.scan()
    if 0x21 not in devices:
        print("Ошибка: OV7670 не найдена на I2C шине!")
        print(f"Найдены устройства: {[hex(d) for d in devices]}")
        return
    
    print("OV7670 найдена, инициализация...")
    
    # Инициализация камеры
    init_ov7670(i2c)
    
    # Параметры изображения
    WIDTH = 640
    HEIGHT = 480
    
    print(f"Начинаем захват изображения {WIDTH}x{HEIGHT}...")
    print("Режим: черно-белый (Y компонента из YUYV)")
    
    frame_count = 0
    
    while True:
        frame_count += 1
        print(f"\n--- Кадр #{frame_count} ---")
        
        rows_captured = capture_frame(WIDTH, HEIGHT, process_line)
        
        if rows_captured == HEIGHT:
            process_frame()
        else:
            print(f"Ошибка: получено только {rows_captured} строк из {HEIGHT}")
        
        time.sleep(0.1)

# Запуск
if __name__ == "__main__":
    main()
