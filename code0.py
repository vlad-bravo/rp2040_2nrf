import board
import busio
import digitalio
import time
import rp2pio
import adafruit_pioasm
import microcontroller

# NeoPixels are 800khz bit streams. We are choosing zeros as <312ns hi, 936 lo>
# and ones as <700 ns hi, 556 ns lo>.
# The first two instructions always run while only one of the two final
# instructions run per bit. We start with the low period because it can be
# longer while waiting for more data.
program = """
.program ws2812
.side_set 1
.wrap_target
bitloop:
   out x 1        side 0 [6]; Drive low. Side-set still takes place before instruction stalls.
   jmp !x do_zero side 1 [3]; Branch on the bit we shifted out previous delay. Drive high.
 do_one:
   jmp  bitloop   side 1 [4]; Continue driving high, for a one (long pulse)
 do_zero:
   nop            side 0 [4]; Or drive low, for a zero (short pulse)
.wrap
"""

assembled = adafruit_pioasm.assemble(program)

sm = rp2pio.StateMachine(
    assembled,
    frequency=12_800_000,  # to get appropriate sub-bit times in PIO program
    first_sideset_pin=microcontroller.pin.GPIO23,
    auto_pull=True,
    out_shift_right=False,
    pull_threshold=8,
)

# --- НАСТРОЙКА SPI 0 (Устройство 0) ---
# Создаем объект SPI0 на пинах GP2, GP3, GP4
spi0 = busio.SPI(clock=board.GP2, MOSI=board.GP3, MISO=board.GP4)

# Настраиваем пин Chip Select (CS) для устройства 0
cs0 = digitalio.DigitalInOut(board.GP5)
cs0.direction = digitalio.Direction.OUTPUT
cs0.value = True  # "Отпускаем" устройство (High = неактивно)

csn0 = digitalio.DigitalInOut(board.GP6)
csn0.direction = digitalio.Direction.OUTPUT
csn0.value = True  # "Отпускаем" устройство (High = неактивно)

irq0 = digitalio.DigitalInOut(board.GP7)
irq0.direction = digitalio.Direction.INPUT


# --- НАСТРОЙКА SPI 1 (Устройство 1) ---
# Создаем объект SPI1 на пинах GP10, GP11, GP12
spi1 = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)

# Настраиваем пин Chip Select (CS) для устройства 2
cs1 = digitalio.DigitalInOut(board.GP13)
cs1.direction = digitalio.Direction.OUTPUT
cs1.value = True  # "Отпускаем" устройство

csn1 = digitalio.DigitalInOut(board.GP8)
csn1.direction = digitalio.Direction.OUTPUT
csn1.value = True  # "Отпускаем" устройство (High = неактивно)

irq1 = digitalio.DigitalInOut(board.GP9)
irq1.direction = digitalio.Direction.INPUT


def write_to_device(spi_bus, cs_pin, data):
    """
    Функция для отправки данных на выбранное устройство.
    """
    # В CircuitPython нужно захватить (lock) шину перед использованием
    while not spi_bus.try_lock():
        pass
    
    try:
        # Настраиваем параметры SPI (скорость, полярность и т.д.)
        # Обычно эти параметры должны совпадать с требованиями вашего устройства
        spi_bus.configure(baudrate=1000000, polarity=0, phase=0)
        
        # Активируем устройство (LOW)
        cs_pin.value = False
        
        # Отправляем данные
        spi_bus.write(data)
        
    finally:
        # Всегда деактивируем устройство и освобождаем шину
        cs_pin.value = True
        spi_bus.unlock()


# --- ОСНОВНОЙ ЦИКЛ ---
while True:
    print("Отправка данных на Устройство 0 (SPI0)...")
    # Пример отправки байтов
    write_to_device(spi0, cs0, b'\x01\x02\x03')
    sm.write(b"\x00\x00\x01") # blue
    
    time.sleep(0.5)

    print("Отправка данных на Устройство 1 (SPI1)...")
    write_to_device(spi1, cs1, b'\xAA\xBB\xCC')
    sm.write(b"\x01\x00\x00") # green
    
    time.sleep(0.5)
    sm.write(b"\x00\x00\x00")
    time.sleep(0.5)
