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

# --- Константы регистров nRF24L01 ---
REG_CONFIG       = 0x00
REG_EN_AA        = 0x01
REG_EN_RXADDR    = 0x02
REG_SETUP_AW     = 0x03
REG_SETUP_RETR   = 0x04
REG_RF_CH        = 0x05
REG_RF_SETUP     = 0x06
REG_STATUS       = 0x07
REG_RX_ADDR_P0   = 0x0A
REG_RX_ADDR_P1   = 0x0B
REG_RX_ADDR_P2   = 0x0C
REG_RX_ADDR_P3   = 0x0D
REG_RX_ADDR_P4   = 0x0E
REG_TX_ADDR      = 0x10
REG_RX_PW_P0     = 0x11 # RX payload width, pipe0
REG_RX_PW_P1     = 0x12 # RX payload width, pipe1
REG_RX_PW_P2     = 0x13 # RX payload width, pipe2
REG_RX_PW_P3     = 0x14 # RX payload width, pipe3
REG_RX_PW_P4     = 0x15 # RX payload width, pipe4
REG_RX_PW_P5     = 0x16 # RX payload width, pipe5
REG_DYNPD        = 0x1C
REG_FEATURE      = 0x1D

CMD_R_REGISTER    = 0x00
CMD_W_REGISTER    = 0x20
CMD_W_TX_PAYLOAD  = 0xA0
CMD_R_RX_PAYLOAD  = 0x61
CMD_FLUSH_TX      = 0xE1
CMD_FLUSH_RX      = 0xE2
CMD_REUSE_TX_PL   = 0xE3 # Used for a PTX device. Reuse last transmitted payload
CMD_W_ACK_PAYLOAD = 0xA8

#MASK_RX_DR       = (1 << 6)
#MASK_TX_DS       = (1 << 5)
#MASK_MAX_RT      = (1 << 4)
MASK_PWR_UP      = (1 << 1)
MASK_PRIM_RX     = (1 << 0)

MASK_RX_DR  = 6 # Mask interrupt caused by RX_DR 1: Interrupt not reflected on the IRQ pin 0: Reflect RX_DR as active low interrupt on the IRQ pin
MASK_TX_DS  = 5 # Mask interrupt caused by TX_DS 1: Interrupt not reflected on the IRQ pin 0: Reflect TX_DS as active low interrupt on the IRQ pin
MASK_MAX_RT = 4 # Mask interrupt caused by MAX_RT 1: Interrupt not reflected on the IRQ pin 0: Reflect MAX_RT as active low interrupt on the IRQ pin
EN_CRC      = 3 # Enable CRC. Forced high if one of the bits in the EN_AA is high
CRCO        = 2 # CRC encoding scheme '0' - 1 byte '1' – 2 bytes
PWR_UP      = 1 # 1: POWER UP, 0:POWER DOWN
PRIM_RX     = 0 # RX/TX control 1: PRX, 0: PTX

CONT_WAVE  = 7 # Enables continuous carrier transmit when high
RF_DR_LOW  = 5 # Air Data Rate [RF_DR_LOW, RF_DR_HIGH]: ‘00’ – 1Mbps// ‘01’ – 2Mbps// ‘10’ – 250kbps// ‘11’ – Reserved
PLL_LOCK   = 4 # Force PLL lock signal. Only used in test
RF_DR_HIGH = 3 # Air Data Rate [RF_DR_LOW, RF_DR_HIGH]: ‘00’ – 1Mbps// ‘01’ – 2Mbps// ‘10’ – 250kbps// ‘11’ – Reserved
RF_PWR2    = 2 # Set RF output power in TX mode
RF_PWR1    = 1 # '00' – -18dBm '01' – -12dBm '10' – -6dBm '11' – 0dBm

RX_DR    = 6 # Data Ready RX FIFO interrupt. Asserted when new data arrives RX FIFO. Write 1 to clear bit
TX_DS    = 5 # Data Sent TX FIFO interrupt. Asserted when packet transmitted on TX. If AUTO_ACK is activated, this bit is set high only when ACK is received. Write 1 to clear bit
MAX_RT   = 4 # Maximum number of TX retransmits interrupt Write 1 to clear bit. If MAX_RT is asserted it must be cleared to enable further communication 
RX_P_NO3 = 3 # Data pipe number for the payload available for reading from RX_FIFO
RX_P_NO2 = 2 # 000-101: Data Pipe Number
RX_P_NO1 = 1 # 111: RX FIFO Empty
TX_FULL  = 0 # TX FIFO full flag. 1: TX FIFO full. 0: Available locations in TX FIFO.

ENAA_P5 = 5 # Enable auto acknowledgement data pipe 5
ENAA_P4 = 4 # Enable auto acknowledgement data pipe 4
ENAA_P3 = 3 # Enable auto acknowledgement data pipe 3
ENAA_P2 = 2 # Enable auto acknowledgement data pipe 2
ENAA_P1 = 1 # Enable auto acknowledgement data pipe 1
ENAA_P0 = 0 # Enable auto acknowledgement data pipe 0

ERX_P5 = 5 # Enable data pipe 5
ERX_P4 = 4 # Enable data pipe 4
ERX_P3 = 3 # Enable data pipe 3
ERX_P2 = 2 # Enable data pipe 2
ERX_P1 = 1 # Enable data pipe 1
ERX_P0 = 0 # Enable data pipe 0

# --- Настройка встроенного светодиода ---
# Если вашей платы нет в списке, можно заменить board.LED на конкретный пин, например board.GP25
try:
    led = digitalio.DigitalInOut(board.LED)
except AttributeError:
    led = digitalio.DigitalInOut(board.GP25) # Стандартный пин для Pico

led.direction = digitalio.Direction.OUTPUT

def blink(times=1, delay=0.1):
    for _ in range(times):
        led.value = True
        time.sleep(delay)
        led.value = False
        time.sleep(delay)

# --- Класс драйвера nRF24L01 ---
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

    def power_up_rx(self):
        self.reg_write(REG_CONFIG, 0<<MASK_RX_DR | 0<<MASK_TX_DS | 0<<MASK_MAX_RT | 1<<EN_CRC | 0<<CRCO | 1<<PWR_UP | 1<<PRIM_RX)
        self.ce.value = True
        time.sleep(0.001)

    def power_up_tx(self):
        self.reg_write(REG_CONFIG, (self.reg_read(REG_CONFIG) | MASK_PWR_UP) & ~MASK_PRIM_RX)

    def clear_interrupts(self):
        self.reg_write(REG_STATUS, MASK_RX_DR | MASK_TX_DS | MASK_MAX_RT)

# --- Инициализация устройств ---

# Устройство 0 (TX) - SPI0
# SCK - GP10, MOSI - GP11, MISO - GP12
spi0 = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)
while not spi0.try_lock():
    pass
spi0.configure(baudrate=4000000, phase=0, polarity=0)
# CS - GP13 (CE), CSN - GP8
nrf0 = NRF24L01(spi0, csn_pin=board.GP8, ce_pin=board.GP13)

# Устройство 1 (RX) - SPI1
# SCK - GP2, MOSI - GP3, MISO - GP4
spi1 = busio.SPI(clock=board.GP2, MOSI=board.GP3, MISO=board.GP4)
while not spi1.try_lock():
    pass
spi1.configure(baudrate=4000000, phase=0, polarity=0)
# CS - GP5 (CE), CSN - GP6
nrf1 = NRF24L01(spi1, csn_pin=board.GP6, ce_pin=board.GP5)

ADDR = b'\xE7\xE7\xE7\xE7\xE7'

def setup_tx():
    sm.write(b"\x00\x01\x01")
    print("--- Setup TX (Device 0) ---")
    nrf0.reg_write(REG_RF_CH, 11)
    nrf0.reg_write(REG_RF_SETUP, 0<<CONT_WAVE | 1<<RF_DR_LOW | 0<<PLL_LOCK | 0<<RF_DR_HIGH | 1<<RF_PWR2 | 1<<RF_PWR1)
    nrf0.reg_write(REG_EN_AA, 1<<ENAA_P5 | 0<<ENAA_P4 | 0<<ENAA_P3 | 0<<ENAA_P2 | 0<<ENAA_P1 | 0<<ENAA_P0) 
    nrf0.reg_write(REG_EN_RXADDR, 1<<ERX_P5 | 1<<ERX_P4 | 1<<ERX_P3 | 1<<ERX_P2 | 1<<ERX_P1 | 1<<ERX_P0)
    # nrf0.reg_write(REG_DYNPD, 0x01)
    # nrf0.reg_write(REG_FEATURE, 0x06) 
    nrf0.write_addr(REG_TX_ADDR, ADDR)
    nrf0.write_addr(REG_RX_ADDR_P0, ADDR)
    nrf0.flush_tx()
    nrf0.flush_rx()
    nrf0.clear_interrupts()
    nrf0.power_up_tx()
    print("TX Ready")

def setup_rx():
    sm.write(b"\x01\x01\x00")
    print("--- Setup RX (Device 1) ---")
    nrf1.reg_write(REG_RF_CH, 110)
    nrf1.reg_write(REG_RF_SETUP, 0<<CONT_WAVE | 1<<RF_DR_LOW | 0<<PLL_LOCK | 0<<RF_DR_HIGH | 1<<RF_PWR2 | 1<<RF_PWR1)
    nrf1.reg_write(REG_EN_AA, 1<<ENAA_P5 | 0<<ENAA_P4 | 0<<ENAA_P3 | 0<<ENAA_P2 | 0<<ENAA_P1 | 0<<ENAA_P0) 
    nrf1.reg_write(REG_EN_RXADDR, 1<<ERX_P5 | 1<<ERX_P4 | 1<<ERX_P3 | 1<<ERX_P2 | 1<<ERX_P1 | 1<<ERX_P0)
    # nrf1.reg_write(REG_DYNPD, 0x01)
    # nrf1.reg_write(REG_FEATURE, 0x06) 
    nrf1.reg_write(REG_SETUP_AW, 3) # address width = 5 bytes
    nrf1.reg_write(REG_RX_PW_P0, 4) # 4 byte payload
    nrf1.write_addr(REG_RX_ADDR_P0, b'\xE7\xC2\xC2\xC2\xE7')
    nrf1.reg_write(REG_RX_PW_P1, 4) # 4 byte payload
    nrf1.write_addr(REG_RX_ADDR_P1, b'\xC2\xE7\xE7\xE7\xC2')
    nrf1.reg_write(REG_RX_PW_P2, 4) # 4 byte payload
    nrf1.write_addr(REG_RX_ADDR_P2, b'\x2C')
    nrf1.reg_write(REG_RX_PW_P3, 4) # 4 byte payload
    nrf1.write_addr(REG_RX_ADDR_P3, b'\x7C')
    nrf1.reg_write(REG_RX_PW_P4, 4) # 4 byte payload
    nrf1.write_addr(REG_RX_ADDR_P4, b'\x5C')
    nrf1.flush_tx()
    nrf1.flush_rx()
    nrf1.clear_interrupts()
    # nrf1.reuse_tx_pl()
    nrf1.power_up_rx()
    print("RX Ready")

# --- Основной цикл ---

setup_rx() 
setup_tx() 

print("Starting loop...")

while True:
    status = nrf1.reg_read(REG_STATUS)
    if status & (1 << MASK_RX_DR):
        nrf1.reg_write(REG_STATUS, 1<<RX_DR | 1<<TX_DS | 1<<MAX_RT | 1<<TX_FULL)
        rx_data = nrf1.read_payload(4)
        print(f"STATUS: {status:02X}  Got: {list(rx_data)}")
        sm.write(b"\x00\x00\x03")
        time.sleep(0.01)
        sm.write(b"\x00\x00\x00")
        
    time.sleep(0.5)
