import board
import busio
import digitalio
import time
import rp2pio
import adafruit_pioasm
import microcontroller

from nrf_defs import (
    REG_CONFIG, REG_EN_AA, REG_EN_RXADDR, REG_SETUP_AW, REG_SETUP_RETR,
    REG_RF_CH, REG_RF_SETUP, REG_STATUS, REG_RX_ADDR_P0, REG_RX_ADDR_P1,
    REG_RX_ADDR_P2, REG_RX_ADDR_P3, REG_RX_ADDR_P4, REG_TX_ADDR,
    REG_RX_PW_P0, REG_RX_PW_P1, REG_RX_PW_P2, REG_RX_PW_P3, REG_RX_PW_P4,
    REG_RX_PW_P5, REG_FIFO_STATUS, REG_DYNPD, REG_FEATURE,

    CMD_R_REGISTER, CMD_W_REGISTER, CMD_W_TX_PAYLOAD, CMD_R_RX_PAYLOAD,
    CMD_FLUSH_TX, CMD_FLUSH_RX, CMD_REUSE_TX_PL, CMD_W_ACK_PAYLOAD, CMD_NOP,

    # CONFIG bits
    MASK_RX_DR, MASK_TX_DS, MASK_MAX_RT, EN_CRC, CRCO, PWR_UP, PRIM_RX,

    # RF_SETUP bits
    CONT_WAVE, RF_DR_LOW, PLL_LOCK, RF_DR_HIGH, RF_PWR2, RF_PWR1,

    # STATUS bits
    RX_DR, TX_DS, MAX_RT, RX_P_NO3, RX_P_NO2, RX_P_NO1, TX_FULL,

    ENAA_P5, ENAA_P4, ENAA_P3, ENAA_P2, ENAA_P1, ENAA_P0,
    ERX_P5, ERX_P4, ERX_P3, ERX_P2, ERX_P1, ERX_P0,
    DPL_P5, DPL_P4, DPL_P3, DPL_P2, DPL_P1, DPL_P0,

    # FEATURE bits
    EN_DPL, EN_ACK_PAY, EN_DYN_ACK,

    # FIFO_STATUS bits
    TX_REUSE, TX_FULL, TX_EMPTY, RX_FULL, RX_EMPTY
)

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

led = digitalio.DigitalInOut(board.GP25) # Стандартный пин для Pico
led.direction = digitalio.Direction.OUTPUT

def blink(times=1, delay=0.1):
    for _ in range(times):
        led.value = True
        time.sleep(delay)
        led.value = False
        time.sleep(delay)

def status_bits(status):
    pipe = (status & (1<<RX_P_NO3 | 1<<RX_P_NO2 | 1<<RX_P_NO1)) // 2
    pipe_text = "RX FIFO Empty" if pipe == 7 else f"pipe={pipe}"
    return (
        f"{status:02X}: "
        f"RX_DR={1 if status & (1<<RX_DR) else 0} "
        f"TX_DS={1 if status & (1<<TX_DS) else 0} "
        f"MAX_RT={1 if status & (1<<MAX_RT) else 0} "
        f"{pipe_text} "
        f"TX_FULL={1 if status & (1<<TX_FULL) else 0}"
    )

def fifo_status_bits(fifo_status):
    return (
        f"{fifo_status:02X}: "
        f"TX_REUSE={1 if fifo_status & (1<<TX_REUSE) else 0} "
        f"TX_FULL={1 if fifo_status & (1<<TX_FULL) else 0} "
        f"TX_EMPTY={1 if fifo_status & (1<<TX_EMPTY) else 0} "
        f"RX_FULL={1 if fifo_status & (1<<RX_FULL) else 0} "
        f"RX_EMPTY={1 if fifo_status & (1<<RX_EMPTY) else 0}"
    )

class NRF24L01:
    def __init__(self, spi, csn_pin, ce_pin):
        self.spi = spi
        self.csn = digitalio.DigitalInOut(csn_pin)
        self.ce = digitalio.DigitalInOut(ce_pin)
        
        self.csn.direction = digitalio.Direction.OUTPUT
        self.ce.direction = digitalio.Direction.OUTPUT
        
        self.csn.value = True 
        self.ce.value = False 

    def reg_write(self, reg, value):
        self.csn.value = False
        self.spi.write(bytes([CMD_W_REGISTER | reg, value]))
        self.csn.value = True

    def reg_read(self, reg):
        self.csn.value = False
        self.spi.write(bytes([CMD_R_REGISTER | reg]))
        result = bytearray(1)
        self.spi.readinto(result)
        self.csn.value = True
        return result[0]

    def write_addr(self, reg, addr):
        self.csn.value = False
        self.spi.write(bytes([CMD_W_REGISTER | reg]))
        self.spi.write(addr)
        self.csn.value = True

    def write_payload(self, data, ack_payload=False, pipe=0):
        self.csn.value = False
        if ack_payload:
            self.spi.write(bytes([CMD_W_ACK_PAYLOAD | pipe]))
        else:
            self.spi.write(bytes([CMD_W_TX_PAYLOAD]))
        self.spi.write(data)
        self.csn.value = True

    def read_payload(self, length):
        self.csn.value = False
        self.spi.write(bytes([CMD_R_RX_PAYLOAD]))
        data = bytearray(length)
        self.spi.readinto(data)
        self.csn.value = True
        return data

    def flush_tx(self):
        self.csn.value = False
        self.spi.write(bytes([CMD_FLUSH_TX]))
        self.csn.value = True

    def flush_rx(self):
        self.csn.value = False
        self.spi.write(bytes([CMD_FLUSH_RX]))
        self.csn.value = True

    def reuse_tx_pl(self):
        self.csn.value = False
        self.spi.write(bytes([CMD_REUSE_TX_PL]))
        self.csn.value = True

    def read_status(self):
        self.csn.value = False
        result = bytearray(1)
        self.spi.readinto(result, write_value=CMD_NOP)
        self.csn.value = True
        return result[0]

    def power_up_rx(self):
        self.reg_write(REG_CONFIG, 0<<MASK_RX_DR | 0<<MASK_TX_DS | 0<<MASK_MAX_RT | 1<<EN_CRC | 1<<CRCO | 1<<PWR_UP | 1<<PRIM_RX)
        self.ce.value = True
        time.sleep(0.001)

    def power_up_tx(self):
        self.reg_write(REG_CONFIG, 0<<MASK_RX_DR | 0<<MASK_TX_DS | 0<<MASK_MAX_RT | 1<<EN_CRC | 1<<CRCO | 1<<PWR_UP | 0<<PRIM_RX)

    def clear_interrupts(self):
        self.reg_write(REG_STATUS, 1<<RX_DR | 1<<TX_DS | 1<<MAX_RT | 1<<TX_FULL)

    def deinit(self):
        self.reg_write(REG_EN_RXADDR, 0<<ERX_P5 | 0<<ERX_P4 | 0<<ERX_P3 | 0<<ERX_P2 | 0<<ERX_P1 | 0<<ERX_P0)
        self.reg_write(REG_EN_AA, 0<<ENAA_P5 | 0<<ENAA_P4 | 0<<ENAA_P3 | 0<<ENAA_P2 | 0<<ENAA_P1 | 0<<ENAA_P0) 
        self.reg_write(REG_SETUP_RETR, 0x00)
        self.reg_write(REG_DYNPD, 0<<DPL_P5 | 0<<DPL_P4 | 0<<DPL_P3 | 0<<DPL_P2 | 0<<DPL_P1 | 0<<DPL_P0)
        self.reg_write(REG_FEATURE, 0<<EN_DPL | 0<<EN_ACK_PAY | 0<<EN_DYN_ACK)
        self.flush_tx()
        self.flush_rx()
        self.clear_interrupts()

# Устройство 0 (TX) - SPI0
spi0 = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)
while not spi0.try_lock():
    pass
spi0.configure(baudrate=4000000, phase=0, polarity=0)
nrf0 = NRF24L01(spi0, csn_pin=board.GP8, ce_pin=board.GP13)

# Устройство 1 (RX) - SPI1
spi1 = busio.SPI(clock=board.GP2, MOSI=board.GP3, MISO=board.GP4)
while not spi1.try_lock():
    pass
spi1.configure(baudrate=4000000, phase=0, polarity=0)
nrf1 = NRF24L01(spi1, csn_pin=board.GP6, ce_pin=board.GP5)

def setup_tx():
    nrf0.deinit()
    sm.write(b"\x00\x01\x01")
    print("--- Setup TX (Device 0) ---")
    nrf0.reg_write(REG_RF_CH, 0x4C)
    nrf0.reg_write(REG_RF_SETUP, 0<<CONT_WAVE | 0<<RF_DR_LOW | 0<<PLL_LOCK | 0<<RF_DR_HIGH | 1<<RF_PWR2 | 1<<RF_PWR1)
    nrf0.reg_write(REG_EN_AA, 0<<ENAA_P5 | 0<<ENAA_P4 | 0<<ENAA_P3 | 0<<ENAA_P2 | 0<<ENAA_P1 | 1<<ENAA_P0) 
    nrf0.reg_write(REG_EN_RXADDR, 0<<ERX_P5 | 0<<ERX_P4 | 0<<ERX_P3 | 0<<ERX_P2 | 0<<ERX_P1 | 1<<ERX_P0)
    nrf0.reg_write(REG_DYNPD, 0<<DPL_P5 | 0<<DPL_P4 | 0<<DPL_P3 | 0<<DPL_P2 | 0<<DPL_P1 | 1<<DPL_P0)
    nrf0.reg_write(REG_FEATURE, 1<<EN_DPL | 1<<EN_ACK_PAY | 0<<EN_DYN_ACK) # 0x06
    nrf0.write_addr(REG_TX_ADDR, b'\xC3\xE7\xEC\xE7\xC5')
    nrf0.write_addr(REG_RX_ADDR_P0, b'\xC3\xE7\xEC\xE7\xC5')
    nrf0.flush_tx()
    nrf0.flush_rx()
    nrf0.clear_interrupts()
    nrf0.power_up_tx()
    print("TX Ready")

def setup_rx():
    nrf1.deinit()
    sm.write(b"\x01\x01\x00")
    print("--- Setup RX (Device 1) ---")
    nrf1.reg_write(REG_RF_CH, 0x4C)
    nrf1.reg_write(REG_RF_SETUP, 0<<CONT_WAVE | 0<<RF_DR_LOW | 0<<PLL_LOCK | 0<<RF_DR_HIGH | 1<<RF_PWR2 | 1<<RF_PWR1)
    nrf1.reg_write(REG_EN_AA, 0<<ENAA_P5 | 0<<ENAA_P4 | 0<<ENAA_P3 | 0<<ENAA_P2 | 1<<ENAA_P1 | 0<<ENAA_P0) 
    nrf1.reg_write(REG_EN_RXADDR, 0<<ERX_P5 | 0<<ERX_P4 | 0<<ERX_P3 | 0<<ERX_P2 | 1<<ERX_P1 | 0<<ERX_P0)
    nrf1.reg_write(REG_DYNPD, 0<<DPL_P5 | 0<<DPL_P4 | 0<<DPL_P3 | 0<<DPL_P2 | 1<<DPL_P1 | 0<<DPL_P0)
    nrf1.reg_write(REG_FEATURE, 1<<EN_DPL | 1<<EN_ACK_PAY | 0<<EN_DYN_ACK) # 0x06
    nrf1.write_addr(REG_RX_ADDR_P1, b'\xC3\xE7\xEC\xE7\xC5')
    nrf1.flush_tx()
    nrf1.flush_rx()
    nrf1.clear_interrupts()
    # nrf1.reuse_tx_pl()
    nrf1.power_up_rx()
    nrf1.write_payload(b'\x22\x36', ack_payload=True, pipe=1)
    nrf1.reuse_tx_pl()
    print("RX Ready")

setup_rx() 
setup_tx() 

while True:
    # fifo_status = nrf1.reg_read(REG_FIFO_STATUS)
    # print(f"FIFO TX status: {fifo_status_bits(fifo_status)}")
    # 1. TX send packet
    # nrf0.clear_interrupts()
    # nrf0.flush_tx()
    # nrf0.flush_rx()
    nrf0.write_payload(b'\x23\x38')
    nrf0.ce.value = True
    time.sleep(0.00001)
    nrf0.ce.value = False
    # print(".", end="")
    # nrf0.clear_interrupts()

    time.sleep(0.1)

    # fifo_status = nrf1.reg_read(REG_FIFO_STATUS)
    # print(f"FIFO RX status: {fifo_status_bits(fifo_status)}")
    # 2. RX receive packet
    status = nrf1.read_status()
    # print(f"RX STATUS: {status:02X}")
    if status & (1 << RX_DR):
        # nrf1.write_payload(b'\x21\x35', ack_payload=True, pipe=1)
        # payload_length = nrf1.reg_read(REG_RX_PW_P1) # dyn payload
        # print(f"RX payload length: {payload_length}")
        rx_data = nrf1.read_payload(2)
        print(f"RX STATUS: {status_bits(status)}  Got: {rx_data[0]:02X}, {rx_data[1]:02X}")
        sm.write(b"\x00\x00\x03")
        nrf1.clear_interrupts()
        nrf1.flush_rx()
        nrf1.flush_tx()

    time.sleep(0.1)

    # fifo_status = nrf1.reg_read(REG_FIFO_STATUS)
    # print(f"FIFO TX status: {fifo_status_bits(fifo_status)}")
    # 3. TX receive ASC payload
    status = nrf0.read_status()
    # print(f"TX STATUS: {status_bits(status)}")
    if status & (1 << RX_DR):
        nrf0.clear_interrupts()
        rx_data = nrf0.read_payload(2)
        print(f"TX STATUS: {status_bits(status)}  Got: {rx_data[0]:02X}, {rx_data[1]:02X}")
        sm.write(b"\x00\x00\x03")
        time.sleep(0.01)
    nrf0.clear_interrupts()
    nrf0.flush_rx()
    nrf0.flush_tx()
    # status = nrf0.read_status()
    # print(f"T4 STATUS: {status_bits(status)}")

    sm.write(b"\x00\x00\x00")
    time.sleep(0.9)
