import rp2pio
import board
import adafruit_pioasm

# Ассемблерный код PIO: бесконечно переключает пин (0 и 1)
pio_asm = """
    .program clk_gen
        set pindirs, 1
    .wrap_target
        set pins, 1
        set pins, 0
    .wrap
"""
assembled = adafruit_pioasm.assemble(pio_asm)

# Запускаем PIO на пине GP21 (куда физически выведен clk_gpout0)
# Параметр frequency автоматически рассчитает делитель для PIO
sm = rp2pio.StateMachine(
    assembled,
    frequency=24_000_000,  # Укажите нужную частоту в Гц (например, 10 МГц)
    first_set_pin=board.GP26,
    out_pin_count=1
)

print("Часы запущены на GP26")

# Чтобы остановить:
# sm.deinit()
