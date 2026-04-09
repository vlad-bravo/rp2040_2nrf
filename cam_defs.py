
REG_GAIN	= 0x00	# Gain lower 8 bits (rest in vref)
REG_BLUE	= 0x01	# blue gain
REG_RED		= 0x02	# red gain
REG_VREF	= 0x03	# Pieces of GAIN, VSTART, VSTOP
REG_COM1	= 0x04	# Control 1
COM1_CCIR656	= 0x40# CCIR656 enable
REG_BAVE	= 0x05	# U/B Average level
REG_GbAVE	= 0x06	# Y/Gb Average level
REG_AECHH	= 0x07	# AEC MS 5 bits
REG_RAVE	= 0x08	# V/R Average level
REG_COM2	= 0x09	# Control 2
COM2_SSLEEP	= 0x10# Soft sleep mode
REG_PID		= 0x0a	# Product ID MSB
REG_VER		= 0x0b	# Product ID LSB
REG_COM3	= 0x0c	# Control 3
COM3_SWAP	= 0x40# Byte swap
COM3_SCALEEN	= 0x08# Enable scaling
COM3_DCWEN	= 0x04# Enable downsamp/crop/window
REG_COM4	= 0x0d	# Control 4
REG_COM5	= 0x0e	# All "reserved"
REG_COM6	= 0x0f	# Control 6

REG_AECH	= 0x10	# More bits of AEC value
REG_CLKRC	= 0x11	# Clocl control
CLK_EXT		= 0x40	# Use external clock directly
CLK_SCALE	= 0x3f	# Mask for internal clock scale
REG_COM7	= 0x12	# Control 7
COM7_RESET	= 0x80# Register reset
COM7_FMT_MASK	= 0x38
COM7_FMT_VGA	= 0x00
COM7_FMT_CIF	= 0x20# CIF format
COM7_FMT_QVGA	= 0x10# QVGA format
COM7_FMT_QCIF	= 0x08# QCIF format
COM7_RGB	= 0x04# bits 0 and 2 - RGB format
COM7_YUV	= 0x00# YUV
COM7_BAYER	= 0x01# Bayer format
COM7_PBAYER	= 0x05# "Processed bayer"
REG_COM8	= 0x13	# Control 8
COM8_FASTAEC	= 0x80	# Enable fast AGC/AEC
COM8_AECSTEP	= 0x40	# Unlimited AEC step size
COM8_BFILT	= 0x20	# Band filter enable
COM8_AGC	= 0x04	# Auto gain enable
COM8_AWB	= 0x02	# White balance enable
COM8_AEC	= 0x01	# Auto exposure enable
REG_COM9	= 0x14	# Control 9- gain ceiling
REG_COM10	= 0x15	# Control 10
COM10_HSYNC	= 0x40# HSYNC instead of HREF
COM10_PCLK_HB	= 0x20# Suppress PCLK on horiz blank
COM10_HREF_REV	= 0x08# Reverse HREF
COM10_VS_LEAD	= 0x04# VSYNC on clock leading edge
COM10_VS_NEG	= 0x02# VSYNC negative
COM10_HS_NEG	= 0x01# HSYNC negative
REG_HSTART	= 0x17	# Horiz start high bits
REG_HSTOP	= 0x18	# Horiz stop high bits
REG_VSTART	= 0x19	# Vert start high bits
REG_VSTOP	= 0x1a	# Vert stop high bits
REG_PSHFT	= 0x1b	# Pixel delay after HREF
REG_MIDH	= 0x1c	# Manuf. ID high
REG_MIDL	= 0x1d	# Manuf. ID low
REG_MVFP	= 0x1e	# Mirror / vflip
MVFP_MIRROR	= 0x20	# Mirror image
MVFP_FLIP	= 0x10	# Vertical flip
REG_LAEC	= 0x1f	# ???

REG_ADCCTR0	= 0x20	# ???
REG_ADCCTR1	= 0x21	# ???
REG_ADCCTR2	= 0x22	# ???
REG_ADCCTR3	= 0x23	# ???
REG_AEW		= 0x24	# AGC upper limit
REG_AEB		= 0x25	# AGC lower limit
REG_VPT		= 0x26	# AGC/AEC fast mode op region
REG_BBIAS	= 0x27	# ???
REG_GbBIAS	= 0x28	# ???
REG_EXHCH	= 0x2a	# ???
REG_EXHCL	= 0x2b	# ???
REG_RBIAS	= 0x2c	# ???
REG_ADVFL	= 0x2d	# ???
REG_ADVFH	= 0x2e	# ???
REG_YAVE	= 0x2f	# ???

REG_HSYST	= 0x30	# HSYNC rising edge delay
REG_HSYEN	= 0x31	# HSYNC falling edge delay
REG_HREF	= 0x32	# HREF pieces
REG_CHLF	= 0x33	# ???
REG_ARBLM	= 0x34	# ???
REG_ADC	= 0x37	# ???
REG_ACOM	= 0x38	# ???
REG_OFON	= 0x39	# ???
REG_TSLB	= 0x3a	# lots of stuff
TSLB_YLAST	= 0x04	# UYVY or VYUY - see com13
TSLB_AOW	= 0x01	# Automatic Output Window
REG_COM11	= 0x3b	# Control 11
COM11_NIGHT	= 0x80	# NIght mode enable
COM11_NMFR	= 0x60	# Two bit NM frame rate
COM11_HZAUTO	= 0x10	# Auto detect 50/60 Hz
COM11_50HZ	= 0x08	# Manual 50Hz select
COM11_EXP	= 0x02
REG_COM12	= 0x3c	# Control 12
COM12_HREF	= 0x80	# HREF always
REG_COM13	= 0x3d	# Control 13
COM13_GAMMA	= 0x80	# Gamma enable
COM13_UVSAT	= 0x40	# UV saturation auto adjustment
COM13_UVSWAP	= 0x01	# V before U - w/TSLB
REG_COM14	= 0x3e	# Control 14
COM14_DCWEN	= 0x10	# DCW/PCLK-scale enable
REG_EDGE	= 0x3f	# Edge enhancement factor

REG_COM15	= 0x40	# Control 15
COM15_R10F0	= 0x00	# Data range 10 to F0
COM15_R01FE	= 0x80	#		01 to FE
COM15_R00FF	= 0xc0	#		00 to FF
COM15_RGB565	= 0x10	# RGB565 output
COM15_RGB555	= 0x30	# RGB555 output
REG_COM16	= 0x41	# Control 16
COM16_AWBGAIN	= 0x08	# AWB gain enable
REG_COM17	= 0x42	# Control 17
COM17_AECWIN	= 0xc0	# AEC window - must match COM4
COM17_CBAR	= 0x08	# DSP Color bar
REG_AWBC1	= 0x43	# ???
REG_AWBC2	= 0x44	# ???
REG_AWBC3	= 0x45	# ???
REG_AWBC4	= 0x46	# ???
REG_AWBC5	= 0x47	# ???
REG_AWBC6	= 0x48	# ???
REG_REG4B	= 0x4b	# ???
REG_DNSTH	= 0x4c	# ???
REG_DM_POS	= 0x4d	# ???
REG_MTX1	= 0x4f	# ???

REG_MTX2	= 0x50	# ???
REG_MTX3	= 0x51	# ???
REG_MTX4	= 0x52	# ???
REG_MTX5	= 0x53	# ???
REG_MTX6	= 0x54	# ???

REG_AWBC7	= 0x59	# ???
REG_AWBC8	= 0x5a	# ???
REG_AWBC9	= 0x5b	# ???
REG_AWBC10	= 0x5c	# ???
REG_AWBC11	= 0x5d	# ???
REG_AWBC12	= 0x5e	# ???
REG_B_LMT	= 0x5f	# ???

REG_R_LMT	= 0x60	# ???
REG_G_LMT	= 0x61	# ???
REG_LCC1	= 0x62	# ???
REG_LCC2	= 0x63	# ???
REG_LCC3	= 0x64	# ???
REG_LCC4	= 0x65	# ???
REG_LCC5	= 0x66	# ???
REG_MANU	= 0x67	# ???
REG_MANV	= 0x68	# ???

REG_GGAIN	= 0x6a	# ???
REG_DBLV	= 0x6b	# ???
REG_AWBCTR3	= 0x6c	# ???
REG_AWBCTR2	= 0x6d	# ???
REG_AWBCTR1	= 0x6e	# ???
REG_AWBCTR0	= 0x6f	# ???

REG_SCALING_XSC	= 0x70	# ???
REG_SCALING_YSC	= 0x71	# ???
REG_SCALING_DCWCTR	= 0x72	# ???
REG_SCALING_PCLK_DIV	= 0x73	# ???
REG_REG74	= 0x74	# ???

REG_REG77	= 0x77	# ???
REG_SLOP	= 0x7a	# ???
REG_GAM1	= 0x7b	# ???
REG_GAM2	= 0x7c	# ???
REG_GAM3	= 0x7d	# ???
REG_GAM4	= 0x7e	# ???
REG_GAM5	= 0x7f	# ???

REG_GAM6	= 0x80	# ???
REG_GAM7	= 0x81	# ???
REG_GAM8	= 0x82	# ???
REG_GAM9	= 0x83	# ???
REG_GAM10	= 0x84	# ???
REG_GAM11	= 0x85	# ???
REG_GAM12	= 0x86	# ???
REG_GAM13	= 0x87	# ???
REG_GAM14	= 0x88	# ???
REG_GAM15	= 0x89	# ???

REG_DM_LNL	= 0x92	# ???
REG_DM_LNH	= 0x93	# ???
REG_LCC6	= 0x94	# ???
REG_LCC7	= 0x95	# ???
REG_BD50ST	= 0x9d	# ???
REG_BD60ST	= 0x9e	# ???

REG_DSPC3	= 0xa1	# ???
REG_SCALING_PCLK_DELAY	= 0xa2	# ???
REG_NT_CTRL	= 0xa4	# ???

REG_STR_OPT	= 0xac	# ???
REG_STR_R	= 0xad	# ???
REG_STR_G	= 0xae	# ???
REG_STR_B	= 0xaf	# ???

REG_ABLC1	= 0xb1	# ???
REG_THL_ST	= 0xb3	# ???
REG_THL_DLT	= 0xb4	# ???
REG_AD_CHB	= 0xbe	# ???
REG_AD_CHR	= 0xbf	# ???

REG_AD_CHGb	= 0xc0	# ???
REG_AD_CHGr	= 0xc1	# ???
REG_SATCTR	= 0xc9	# ???

REG_CMATRIX_BASE	= 0x4f
CMATRIX_LEN = 6
REG_CMATRIX_SIGN	= 0x58

REG_BRIGHT	= 0x55	# Brightness
REG_CONTRAS	= 0x56	# Contrast control
REG_CONTRAS_CENTER	= 0x57	# ???
REG_MTXS	= 0x58	# ???

REG_GFIX	= 0x69	# Fix gain control

REG_REG75	= 0x75
REG_REG76	= 0x76	# OV's name
R76_BLKPCOR	= 0x80	# Black pixel correction enable
R76_WHTPCOR	= 0x40	# White pixel correction enable

REG_RGB444	= 0x8c	# RGB 444 control
R444_ENABLE	= 0x02	# Turn on RGB444, overrides 5x5
R444_RGBX	= 0x01	# Empty nibble at end

REG_HAECC1	= 0x9f	# Hist AEC/AGC control 1
REG_HAECC2	= 0xa0	# Hist AEC/AGC control 2

REG_BD50MAX	= 0xa5	# 50hz banding step limit
REG_HAECC3	= 0xa6	# Hist AEC/AGC control 3
REG_HAECC4	= 0xa7	# Hist AEC/AGC control 4
REG_HAECC5	= 0xa8	# Hist AEC/AGC control 5
REG_HAECC6	= 0xa9	# Hist AEC/AGC control 6
REG_HAECC7	= 0xaa	# Hist AEC/AGC control 7
REG_BD60MAX	= 0xab	# 60hz banding step limit
