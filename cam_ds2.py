import board
import busio
import digitalio
import time
import microcontroller

# === Конфигурация пинов ===
PINS = {
    'D0': board.GP14, 'D1': board.GP15, 'D2': board.GP16, 'D3': board.GP17,
    'D4': board.GP18, 'D5': board.GP19, 'D6': board.GP20, 'D7': board.GP21,
    'PCLK': board.GP27, 'VSYNC': board.GP23, 'HREF': board.GP28, 'MCLK': board.GP26
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
        pin = PINS[f'D{i}']
        pin_dio = digitalio.DigitalInOut(pin)
        pin_dio.direction = digitalio.Direction.INPUT
        PINS[f'D{i}_dio'] = pin_dio
    
    # Управляющие пины
    PINS['PCLK_dio'] = digitalio.DigitalInOut(PINS['PCLK'])
    PINS['PCLK_dio'].direction = digitalio.Direction.INPUT
    
    PINS['VSYNC_dio'] = digitalio.DigitalInOut(PINS['VSYNC'])
    PINS['VSYNC_dio'].direction = digitalio.Direction.INPUT
    
    PINS['HREF_dio'] = digitalio.DigitalInOut(PINS['HREF'])
    PINS['HREF_dio'].direction = digitalio.Direction.INPUT
    
    # Выходные пины
    #PINS['RESET_dio'] = digitalio.DigitalInOut(PINS['RESET'])
    #PINS['RESET_dio'].direction = digitalio.Direction.OUTPUT
    
    #PINS['PWDN_dio'] = digitalio.DigitalInOut(PINS['PWDN'])
    #PINS['PWDN_dio'].direction = digitalio.Direction.OUTPUT
    
    # MCLK - используем PWM для генерации тактовой частоты
    from pwmio import PWMOut
    PINS['MCLK_pwm'] = PWMOut(PINS['MCLK'], frequency=8_000_000, duty_cycle=32768)

# === I2C коммуникация ===
def write_reg(i2c, reg, value):
    """Запись в регистр OV7670"""
    i2c.writeto(0x21, bytes([reg, value]))

def read_reg(i2c, reg):
    """Чтение регистра OV7670"""
    buf = bytearray(1)
    buf[0] = reg
    i2c.writeto_then_readfrom(0x21, buf, buf)
    #result = i2c.readfrom(0x21, buf)
    return buf[0]

# === Настройка режимов камеры ===
def reset_camera(i2c):
    """Сброс камеры в известное состояние"""
    # Аппаратный сброс
    #PINS['RESET_dio'].value = False
    #time.sleep(0.01)
    #PINS['RESET_dio'].value = True
    #time.sleep(0.1)
    
    # Программный сброс через регистр COM7
    write_reg(i2c, REG_COM7, 0x80)
    time.sleep(0.1)

def init_ov7670(i2c):
    """Инициализация OV7670 для режима 640x480 YUV"""
    
    # Сброс камеры
    reset_camera(i2c)
    
    # Включение камеры (выход из power down)
    #PINS['PWDN_dio'].value = False
    #time.sleep(0.001)
    
    # Настройка тактового делителя (CLKRC)
    # 0x01 = делитель на 2, 0x00 = без деления
    # Для 8MHz MCLK от RP2040, ставим делитель 1
    write_reg(i2c, REG_CLKRC, 0x00)
    
    # COM7: RGB | Resolution VGA | без сброса
    write_reg(i2c, REG_COM7, 0x06)  # 0x06 = VGA, RGB
    
    # COM3: Включить масштабирование, вертикальный зеркальный (при необходимости)
    write_reg(i2c, REG_COM3, 0x04)
    
    # COM4: Без масштабирования
    write_reg(i2c, REG_COM4, 0x00)
    
    # COM5: Настройки AGC/AEC
    write_reg(i2c, REG_COM5, 0x61)  # 0x61 = AGC включен, AEC включен
    
    # COM6: Настройки AGC
    write_reg(i2c, REG_COM6, 0x4B)
    
    # COM8: Включить AGC и AEC
    write_reg(i2c, REG_COM8, 0xE7)  # 0xE7 = AGC, AEC, AWB, AEC большой диапазон
    
    # COM9: Gain ceiling
    write_reg(i2c, REG_COM9, 0x4A)
    
    # COM10: PCLK output polarity
    write_reg(i2c, REG_COM10, 0x00)
    
    # COM11: ночной режим, PCLK инвертировать
    write_reg(i2c, REG_COM11, 0x02)  # 0x02 = инвертировать PCLK
    
    # COM12: HREF polarity
    write_reg(i2c, REG_COM12, 0x08)  # 0x08 = HREF active high
    
    # COM13: формат данных RGB/YUV
    write_reg(i2c, REG_COM13, 0x18)  # 0x18 = YUV формат
    
    # COM14: Enable YUV output
    write_reg(i2c, REG_COM14, 0x18)
    
    # COM15: Выходной формат: YUYV
    write_reg(i2c, REG_COM15, 0xC0)  # 0xC0 = YUYV
    
    # COM16: Замена U и V
    write_reg(i2c, REG_COM16, 0x00)
    
    # TSLB: Порядок байтов в YUV
    write_reg(i2c, REG_TSLB, 0x00)  # 0x00 = YUYV порядок
    
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
    #print(f"ID камеры: 0x{read_reg(i2c, REG_PID):02X}{read_reg(i2c, REG_VER):02X}")

# === Захват строки ===
def capture_line(pclk, href, data_pins):
    """Захват одной строки 640 байт (только Y компонента)"""
    line_buffer = bytearray(640)
    pixel_index = 0
    
    # Ждем начала строки (HREF = HIGH)
    while not href.value:
        pass
    
    # Захватываем 640 пикселей (640 байт Y)
    while pixel_index < 640:
        # Ждем перепада PCLK (предполагаем что PCLK инвертирован)
        last_pclk = pclk.value
        while pclk.value == last_pclk:
            pass
        
        # Читаем данные с шины
        data = 0
        for i in range(8):
            if data_pins[i].value:
                data |= (1 << i)
        
        # Берем только первый байт (Y) из каждого 16-битного слова YUYV
        if pixel_index % 2 == 0:  # Y компонента
            line_buffer[pixel_index // 2] = data
        
        pixel_index += 1
    
    return line_buffer

# === Захват полного кадра ===
def capture_frame(width, height, process_line_cb):
    """Захват полного кадра с построчной обработкой"""
    
    # Два буфера по 640 байт
    buffer1 = bytearray(width)
    buffer2 = bytearray(width)
    
    # Указатели на активный буфер для заполнения и для обработки
    fill_buffer = buffer1
    process_buffer = buffer2
    
    # Получаем объекты пинов
    vsync_pin = PINS['VSYNC_dio']
    href_pin = PINS['HREF_dio']
    pclk_pin = PINS['PCLK_dio']
    data_pins = [PINS[f'D{i}_dio'] for i in range(8)]
    
    row_count = 0
    
    # Ждем начала кадра (VSYNC)
    # Ждем VSYNC = HIGH (начало кадра)
    while not vsync_pin.value:
        pass
    
    # Ждем VSYNC = LOW (начало активной области)
    while vsync_pin.value:
        pass
    
    # Захватываем все строки
    while row_count < height:
        # Ждем начала строки
        while not href_pin.value:
            # Если VSYNC стал HIGH, значит кадр закончился
            if vsync_pin.value:
                break
        
        # Захватываем строку
        captured_line = capture_line(pclk_pin, href_pin, data_pins)
        
        # Копируем в активный буфер
        fill_buffer[:] = captured_line
        
        # Меняем указатели местами
        fill_buffer, process_buffer = process_buffer, fill_buffer
        
        # Обрабатываем предыдущую строку
        if row_count > 0:  # Первая строка еще не готова для обработки
            process_line_cb(row_count - 1, process_buffer)
        
        row_count += 1
    
    # Обрабатываем последнюю строку
    process_line_cb(row_count - 1, fill_buffer)
    
    return row_count

# === Процедуры обработки ===
def process_line(row_number, line_data):
    """Обработка одной строки"""
    # Пример: вычисляем среднюю яркость строки
    if line_data:
        avg_brightness = sum(line_data) / len(line_data)
        if row_number % 50 == 0:  # Выводим каждую 50-ю строку для отладки
            print(f"Строка {row_number:3d}: средняя яркость = {avg_brightness:.1f}")
        
        # Здесь можно добавить свою логику обработки строки
        # Например: отправить по UART, сохранить в файл, распознавание и т.д.

def process_frame():
    """Обработка полного кадра"""
    print("=== Кадр полностью получен и обработан ===")
    # Здесь можно выполнить анализ всего кадра

# === Основная функция ===
def main():
    # Инициализация пинов и тактирования
    print("Инициализация пинов...")
    init_pins()
    
    # Инициализация I2C
    i2c = busio.I2C(board.GP1, board.GP0)  # SDA, SCL
    while not i2c.try_lock():
        pass
    
    # Поиск камеры на I2C шине
    devices = i2c.scan()
    if 0x21 not in devices:
        print("Ошибка: OV7670 не найдена на I2C шине!")
        print(f"Найдены устройства: {[hex(d) for d in devices]}")
        return
    
    print("OV7670 найдена, инициализация...")
    
    # Инициализация камеры
    init_ov7670(i2c)
    
    i2c.unlock()
    
    # Параметры изображения
    WIDTH = 640
    HEIGHT = 480
    
    print(f"Начинаем захват изображения {WIDTH}x{HEIGHT}...")
    print("Режим: черно-белый (Y компонента из YUYV)")
    
    # Счетчик кадров
    frame_count = 0
    
    # Бесконечный цикл захвата
    while True:
        frame_count += 1
        print(f"\n--- Кадр #{frame_count} ---")
        
        # Захват кадра с построчной обработкой
        rows_captured = capture_frame(WIDTH, HEIGHT, process_line)
        
        if rows_captured == HEIGHT:
            process_frame()
        else:
            print(f"Ошибка: получено только {rows_captured} строк из {HEIGHT}")
        
        # Небольшая задержка между кадрами
        time.sleep(0.1)

# Запуск
if __name__ == "__main__":
    main()
