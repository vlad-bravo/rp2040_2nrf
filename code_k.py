import board
import digitalio
import time
import rp2pio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import microcontroller
import adafruit_pioasm

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

keyboard = Keyboard(usb_hid.devices)

mute_pin = board.GP24       # pin to connect button to
mute_led_pin = board.GP25   # pin to connect LED to

# Initializing LED
mute_led = digitalio.DigitalInOut(mute_led_pin)
mute_led.direction = digitalio.Direction.OUTPUT

# Initializing Button
mute = digitalio.DigitalInOut(mute_pin)
mute.direction = digitalio.Direction.INPUT
mute.pull = digitalio.Pull.UP

while True:
    if not mute.value:
        mute_led.value = 1
        sm.write(b"\x00\x0a\x00")

        print('NUM_LOCK', keyboard.led_on(keyboard.LED_NUM_LOCK))
        print('CAPS_LOCK', keyboard.led_on(keyboard.LED_CAPS_LOCK))
        print('SCROLL_LOCK', keyboard.led_on(keyboard.LED_SCROLL_LOCK))

        time.sleep(0.15)
        mute_led.value = 0
        sm.write(b"\x00\x00\x00")

    time.sleep(0.1)
