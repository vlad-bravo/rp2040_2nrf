import rp2pio
import board

# Ассемблерный код PIO: бесконечно переключает пин (0 и 1)
pio_asm = """
    .program clk_gen
    .wrap_target
        nop [1]  ; Задержки (cycles) влияют на максимальную частоту
        nop [1]
        pins, 1 [1]
        nop [1]
        nop [1]
        pins, 0 [1]
    .wrap
"""

# Запускаем PIO на пине GP21 (куда физически выведен clk_gpout0)
# Параметр frequency автоматически рассчитает делитель для PIO
sm = rp2pio.StateMachine(
    pio_asm,
    frequency=10_000_000,  # Укажите нужную частоту в Гц (например, 10 МГц)
    first_out_pin=board.GP21,
    out_pin_count=1
)

print("Часы запущены на GP21")

# Чтобы остановить:
# sm.deinit()
