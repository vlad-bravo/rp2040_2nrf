import digitalio
import time

from nrf_defs import (
    REG_CONFIG, REG_EN_AA, REG_EN_RXADDR, REG_SETUP_AW, REG_SETUP_RETR,
    REG_RF_CH, REG_RF_SETUP, REG_STATUS, REG_RX_ADDR_P0, REG_RX_ADDR_P1,
    REG_RX_ADDR_P2, REG_RX_ADDR_P3, REG_RX_ADDR_P4, REG_TX_ADDR,
    REG_RX_PW_P0, REG_RX_PW_P1, REG_RX_PW_P2, REG_RX_PW_P3, REG_RX_PW_P4,
    REG_RX_PW_P5, REG_FIFO_STATUS, REG_DYNPD, REG_FEATURE,

    CMD_R_REGISTER, CMD_W_REGISTER, CMD_ACTIVATE, CMD_W_TX_PAYLOAD, CMD_R_RX_PAYLOAD,
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

    def activate(self):
        self.csn.value = False
        self.spi.write(bytes([CMD_ACTIVATE, 0x73]))
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
        self.ce.value = False
        self.reg_write(REG_EN_RXADDR, 0<<ERX_P5 | 0<<ERX_P4 | 0<<ERX_P3 | 0<<ERX_P2 | 0<<ERX_P1 | 0<<ERX_P0)
        self.reg_write(REG_EN_AA, 0<<ENAA_P5 | 0<<ENAA_P4 | 0<<ENAA_P3 | 0<<ENAA_P2 | 0<<ENAA_P1 | 0<<ENAA_P0)
        self.reg_write(REG_SETUP_RETR, 0x00)
        self.reg_write(REG_DYNPD, 0<<DPL_P5 | 0<<DPL_P4 | 0<<DPL_P3 | 0<<DPL_P2 | 0<<DPL_P1 | 0<<DPL_P0)
        self.reg_write(REG_FEATURE, 0<<EN_DPL | 0<<EN_ACK_PAY | 0<<EN_DYN_ACK)
        self.flush_tx()
        self.flush_rx()
        self.clear_interrupts()
        self.reg_write(REG_CONFIG, 0<<MASK_RX_DR | 0<<MASK_TX_DS | 0<<MASK_MAX_RT | 0<<EN_CRC | 0<<CRCO | 0<<PWR_UP | 0<<PRIM_RX)
