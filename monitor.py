import board
import busio
import digitalio
import time

from neopixel import neopixel_sm
from nrf24l01 import NRF24L01
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

sm = neopixel_sm()
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
    nrf0.reg_write(REG_RF_SETUP, 0<<CONT_WAVE | 0<<RF_DR_LOW | 0<<PLL_LOCK | 0<<RF_DR_HIGH | 0<<RF_PWR2 | 0<<RF_PWR1)
    nrf0.reg_write(REG_EN_AA, 0<<ENAA_P5 | 0<<ENAA_P4 | 0<<ENAA_P3 | 0<<ENAA_P2 | 0<<ENAA_P1 | 1<<ENAA_P0) 
    nrf0.reg_write(REG_EN_RXADDR, 0<<ERX_P5 | 0<<ERX_P4 | 0<<ERX_P3 | 0<<ERX_P2 | 0<<ERX_P1 | 1<<ERX_P0)
    nrf0.reg_write(REG_DYNPD, 0<<DPL_P5 | 0<<DPL_P4 | 0<<DPL_P3 | 0<<DPL_P2 | 0<<DPL_P1 | 1<<DPL_P0)
    nrf0.reg_write(REG_FEATURE, 1<<EN_DPL | 1<<EN_ACK_PAY | 0<<EN_DYN_ACK)
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
    nrf1.reg_write(REG_RF_SETUP, 0<<CONT_WAVE | 0<<RF_DR_LOW | 0<<PLL_LOCK | 0<<RF_DR_HIGH | 0<<RF_PWR2 | 0<<RF_PWR1)
    nrf1.reg_write(REG_EN_AA, 0<<ENAA_P5 | 0<<ENAA_P4 | 0<<ENAA_P3 | 0<<ENAA_P2 | 1<<ENAA_P1 | 0<<ENAA_P0) 
    nrf1.reg_write(REG_EN_RXADDR, 0<<ERX_P5 | 0<<ERX_P4 | 0<<ERX_P3 | 0<<ERX_P2 | 1<<ERX_P1 | 0<<ERX_P0)
    nrf1.reg_write(REG_DYNPD, 0<<DPL_P5 | 0<<DPL_P4 | 0<<DPL_P3 | 0<<DPL_P2 | 1<<DPL_P1 | 0<<DPL_P0)
    nrf1.reg_write(REG_FEATURE, 1<<EN_DPL | 1<<EN_ACK_PAY | 0<<EN_DYN_ACK)
    nrf1.write_addr(REG_RX_ADDR_P1, b'\xC3\xE7\xEC\xE7\xC5')
    nrf1.flush_tx()
    nrf1.flush_rx()
    nrf1.clear_interrupts()
    nrf1.power_up_rx()
    nrf1.write_payload(b'\x22\x36', ack_payload=True, pipe=1)
    nrf1.reuse_tx_pl()
    print("RX Ready")

setup_rx() 
setup_tx() 

tx_value = 0
rx_value = 0
while True:
    # 1. TX send packet
    nrf0.write_payload(bytes([0x21, tx_value]))
    nrf0.ce.value = True
    time.sleep(0.00001)
    nrf0.ce.value = False

    time.sleep(0.001)

    # 2. RX receive packet
    status = nrf1.read_status()
    if status & (1 << RX_DR):
        rx_data = nrf1.read_payload(2)
        print(f"RX STATUS: {status_bits(status)}  Got: {rx_data[0]:02X}, {rx_data[1]:02X}")
        sm.write(b"\x00\x00\x03")

    time.sleep(0.0001)

    # 3. TX receive ASC payload
    status = nrf0.read_status()
    if status & (1 << RX_DR):
        rx_data = nrf0.read_payload(2)
        print(f"TX STATUS: {status_bits(status)}  Got: {rx_data[0]:02X}, {rx_data[1]:02X}")
        sm.write(b"\x03\x00\x00")
        time.sleep(0.01)

    tx_value = tx_value + 1 if tx_value < 25 else 0
    if tx_value % 3 == 0:
        nrf1.write_payload(bytes([0x22, rx_value]), ack_payload=True, pipe=1)
        rx_value = rx_value + 1 if rx_value < 25 else 0

    sm.write(b"\x00\x00\x00")
    time.sleep(0.9)
