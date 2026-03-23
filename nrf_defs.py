
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
REG_FIFO_STATUS  = 0x17
REG_DYNPD        = 0x1C
REG_FEATURE      = 0x1D

CMD_R_REGISTER    = 0x00
CMD_W_REGISTER    = 0x20
CMD_R_RX_PL_WID   = 0x60 # Read RX payload width for the top R_RX_PAYLOAD in the RX FIFO. NOTE: Flush RX FIFO if the read value is larger than 32 bytes
CMD_R_RX_PAYLOAD  = 0x61
CMD_W_TX_PAYLOAD  = 0xA0
CMD_W_ACK_PAYLOAD = 0xA8
CMD_W_TX_PAYLOAD_NO_ACK = 0xB0 # Used in TX mode. Disables AUTOACK on this specific packet
CMD_FLUSH_TX      = 0xE1
CMD_FLUSH_RX      = 0xE2
CMD_REUSE_TX_PL   = 0xE3 # Used for a PTX device. Reuse last transmitted payload
CMD_NOP           = 0xFF

# STATUS bits
RX_DR    = 6 # Data Ready RX FIFO interrupt. Asserted when new data arrives RX FIFO. Write 1 to clear bit
TX_DS    = 5 # Data Sent TX FIFO interrupt. Asserted when packet transmitted on TX. If AUTO_ACK is activated, this bit is set high only when ACK is received. Write 1 to clear bit
MAX_RT   = 4 # Maximum number of TX retransmits interrupt Write 1 to clear bit. If MAX_RT is asserted it must be cleared to enable further communication 
RX_P_NO3 = 3 # Data pipe number for the payload available for reading from RX_FIFO
RX_P_NO2 = 2 # 000-101: Data Pipe Number
RX_P_NO1 = 1 # 111: RX FIFO Empty
TX_FULL  = 0 # TX FIFO full flag. 1: TX FIFO full. 0: Available locations in TX FIFO.

# CONFIG bits
MASK_RX_DR  = 6 # Mask interrupt caused by RX_DR 1: Interrupt not reflected on the IRQ pin 0: Reflect RX_DR as active low interrupt on the IRQ pin
MASK_TX_DS  = 5 # Mask interrupt caused by TX_DS 1: Interrupt not reflected on the IRQ pin 0: Reflect TX_DS as active low interrupt on the IRQ pin
MASK_MAX_RT = 4 # Mask interrupt caused by MAX_RT 1: Interrupt not reflected on the IRQ pin 0: Reflect MAX_RT as active low interrupt on the IRQ pin
EN_CRC      = 3 # Enable CRC. Forced high if one of the bits in the EN_AA is high
CRCO        = 2 # CRC encoding scheme '0' - 1 byte '1' – 2 bytes
PWR_UP      = 1 # 1: POWER UP, 0:POWER DOWN
PRIM_RX     = 0 # RX/TX control 1: PRX, 0: PTX

# RF_SETUP bits
CONT_WAVE  = 7 # Enables continuous carrier transmit when high
RF_DR_LOW  = 5 # Air Data Rate [RF_DR_LOW, RF_DR_HIGH]: ‘00’ – 1Mbps// ‘01’ – 2Mbps// ‘10’ – 250kbps// ‘11’ – Reserved
PLL_LOCK   = 4 # Force PLL lock signal. Only used in test
RF_DR_HIGH = 3 # Air Data Rate [RF_DR_LOW, RF_DR_HIGH]: ‘00’ – 1Mbps// ‘01’ – 2Mbps// ‘10’ – 250kbps// ‘11’ – Reserved
RF_PWR2    = 2 # Set RF output power in TX mode
RF_PWR1    = 1 # '00' – -18dBm '01' – -12dBm '10' – -6dBm '11' – 0dBm

# FEATURE bits
EN_DPL     = 2 # Enables Dynamic Payload Length
EN_ACK_PAY = 1 # Enables Payload with ACK
EN_DYN_ACK = 0 # Enables the W_TX_PAYLOAD_NOACK command

# FIFO_STATUS bits
TX_REUSE = 6
TX_FULL  = 5
TX_EMPTY = 4
RX_FULL  = 1
RX_EMPTY = 0

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

DPL_P5 = 5 # Enable dyn. payload length data pipe 5. (Requires EN_DPL and ENAA_P5)
DPL_P4 = 4 # Enable dyn. payload length data pipe 4. (Requires EN_DPL and ENAA_P4)
DPL_P3 = 3 # Enable dyn. payload length data pipe 3. (Requires EN_DPL and ENAA_P3)
DPL_P2 = 2 # Enable dyn. payload length data pipe 2. (Requires EN_DPL and ENAA_P2)
DPL_P1 = 1 # Enable dyn. payload length data pipe 1. (Requires EN_DPL and ENAA_P1)
DPL_P0 = 0 # Enable dyn. payload length data pipe 0. (Requires EN_DPL and ENAA_P0)
