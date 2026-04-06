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
    TX_REUSE, TX_FUL2, TX_EMPTY, RX_FULL, RX_EMPTY
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
        f"TX_FULL={1 if fifo_status & (1<<TX_FUL2) else 0} "
        f"TX_EMPTY={1 if fifo_status & (1<<TX_EMPTY) else 0} "
        f"RX_FULL={1 if fifo_status & (1<<RX_FULL) else 0} "
        f"RX_EMPTY={1 if fifo_status & (1<<RX_EMPTY) else 0}"
    )

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

def setup_tx():
    nrf0.deinit()
    sm.write(b"\x00\x01\x01")
    print("--- Setup TX (Device 0) ---")
    nrf0.reg_write(REG_RF_CH, 11)
    nrf0.reg_write(REG_RF_SETUP, 0<<CONT_WAVE | 1<<RF_DR_LOW | 0<<PLL_LOCK | 0<<RF_DR_HIGH | 1<<RF_PWR2 | 1<<RF_PWR1)
    nrf0.reg_write(REG_EN_AA, 1<<ENAA_P5 | 0<<ENAA_P4 | 0<<ENAA_P3 | 0<<ENAA_P2 | 0<<ENAA_P1 | 0<<ENAA_P0)
    nrf0.reg_write(REG_EN_RXADDR, 1<<ERX_P5 | 1<<ERX_P4 | 1<<ERX_P3 | 1<<ERX_P2 | 1<<ERX_P1 | 1<<ERX_P0)
    nrf0.write_addr(REG_TX_ADDR, b'\xE7\xE7\xE7\xE7\xE7')
    nrf0.write_addr(REG_RX_ADDR_P0, b'\xE7\xE7\xE7\xE7\xE7')
    nrf0.flush_tx()
    nrf0.flush_rx()
    nrf0.clear_interrupts()
    #nrf0.power_up_tx()
    #nrf0.reg_write(REG_CONFIG, 0<<MASK_RX_DR | 0<<MASK_TX_DS | 0<<MASK_MAX_RT | 1<<EN_CRC | 1<<CRCO | 1<<PWR_UP | 0<<PRIM_RX)
    print("TX Ready")

def setup_rx():
    nrf1.deinit()
    sm.write(b"\x01\x01\x00")
    print("--- Setup RX (Device 1) ---")
    nrf1.reg_write(REG_RF_CH, 120)
    nrf1.reg_write(REG_RF_SETUP, 0<<CONT_WAVE | 0<<RF_DR_LOW | 0<<PLL_LOCK | 1<<RF_DR_HIGH | 1<<RF_PWR2 | 1<<RF_PWR1)
    nrf1.reg_write(REG_EN_AA, 0<<ENAA_P5 | 0<<ENAA_P4 | 0<<ENAA_P3 | 0<<ENAA_P2 | 0<<ENAA_P1 | 1<<ENAA_P0)
    nrf1.reg_write(REG_EN_RXADDR, 0<<ERX_P5 | 0<<ERX_P4 | 0<<ERX_P3 | 0<<ERX_P2 | 0<<ERX_P1 | 1<<ERX_P0)
    nrf1.reg_write(REG_RX_PW_P0, 32) # 32 bytes payload
    nrf1.write_addr(REG_RX_ADDR_P0, b'\x5C\xE7\xE3\xE7\xC5')
    nrf1.reg_write(REG_DYNPD, 0<<DPL_P5 | 0<<DPL_P4 | 0<<DPL_P3 | 0<<DPL_P2 | 0<<DPL_P1 | 1<<DPL_P0)
    nrf1.reg_write(REG_FEATURE, 1<<EN_DPL | 1<<EN_ACK_PAY | 1<<EN_DYN_ACK)
    nrf1.activate()
    nrf1.flush_tx()
    nrf1.flush_rx()
    nrf1.clear_interrupts()
    # nrf1.power_up_rx()
    nrf1.reg_write(REG_CONFIG, 1<<MASK_RX_DR | 1<<MASK_TX_DS | 1<<MASK_MAX_RT | 1<<EN_CRC | 0<<CRCO | 1<<PWR_UP | 1<<PRIM_RX)
    nrf1.ce.value = True
    time.sleep(0.001)
    nrf1.write_payload(b'\x22\x36', ack_payload=True, pipe=0)
    nrf1.reuse_tx_pl()
    print("RX Ready")

# --- Основной цикл ---

setup_rx() 
setup_tx() 

print("Starting loop...")

while True:
    #nrf1.flush_rx()
    fifo = nrf1.reg_read(REG_FIFO_STATUS)
    #print(fifo_status_bits(fifo))
    status = nrf1.read_status()
    # print(f"STATUS: {status_bits(status)}")
    if status & (1 << RX_DR):
        # print(f"STATUS: {status_bits(status)}")
        nrf1.clear_interrupts()
        rx_data = nrf1.read_payload(32)
        if status & 0x0E == 0x00: # pipe 0
            if rx_data[0] in (97, 98, 99):
                #print(f"STATUS: {status_bits(status)}  Got: {list(rx_data[:4])}")
                pass
            elif rx_data[0] == 43:
                print(f"STATUS: {status_bits(status)}  Got: {rx_data[0]} {rx_data[5]:02X} {rx_data[6]:02X}")
                #sm.write(b"\x00\x00\x03")
                #time.sleep(0.01)
                #sm.write(b"\x00\x00\x00")
            else:
                print(f"STATUS: {status_bits(status)}  Got: {rx_data[0]} {rx_data[2]:02X} {rx_data[4]:02X}")
                #sm.write(b"\x03\x00\x00")
                #time.sleep(0.01)
                #sm.write(b"\x00\x00\x00")
        else:
            #print(f"STATUS: {status_bits(status)}")
            pass
        # nrf1.flush_tx()
        
    # time.sleep(0.5)
