import rp2pio
import adafruit_pioasm
import microcontroller

def neopixel_sm():
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

    return rp2pio.StateMachine(
        assembled,
        frequency=12_800_000,  # to get appropriate sub-bit times in PIO program
        first_sideset_pin=microcontroller.pin.GPIO23,
        auto_pull=True,
        out_shift_right=False,
        pull_threshold=8,
    )
