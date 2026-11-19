"""
============================================================
Project: MicroPython FM Receiver 2026
File: config.py

Description:
Central configuration file.
Contains GPIO assignments, SPI/I2C parameters,
radio frequencies, volume and encoder settings.

Author: MicroPython FM Receiver 2026 Team

Implementation:
Original project configuration.

Technical References:
- Raspberry Pi Pico / RP2040 Documentation
- MicroPython machine module documentation
============================================================
"""

# ==========================================================
# SI4703 FM TUNER - I2C0
# ==========================================================

I2C_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
TUNER_RESET_PIN = 6

TUNER_ADDRESS = 0x10
I2C_FREQUENCY = 100000


# ==========================================================
# NOKIA 5110 DISPLAY - SPI0
# ==========================================================

SPI_ID = 0

SPI_SCK_PIN = 18
SPI_MOSI_PIN = 19

DISPLAY_DC_PIN = 20
DISPLAY_CS_PIN = 17
DISPLAY_RESET_PIN = 21

DISPLAY_BAUDRATE = 1000000
DISPLAY_CONTRAST = 0xB8
DISPLAY_ROTATE_180 = True


# ==========================================================
# KY-040 ROTARY ENCODER
# ==========================================================

ENCODER_CLK_PIN = 16
ENCODER_DT_PIN = 15
ENCODER_BUTTON_PIN = 14

ENCODER_DIRECTION = 1
ENCODER_STEPS_PER_CLICK = 4

BUTTON_DEBOUNCE_MS = 35
DOUBLE_CLICK_MS = 350
LONG_PRESS_MS = 800


# ==========================================================
# FM RADIO SETTINGS
# ==========================================================

START_FREQUENCY = 990       # 99.0 MHz

MIN_FREQUENCY = 875         # 87.5 MHz
MAX_FREQUENCY = 1080        # 108.0 MHz

FREQUENCY_STEP = 1          # 0.1 MHz

START_VOLUME = 4

MIN_VOLUME = 0
MAX_VOLUME = 15


# ==========================================================
# RADIO PRESETS
# Use None for empty slots.
# Frequencies are stored in 0.1 MHz units.
# ==========================================================

PRESETS = [
    875,
    901,
    995,
    1025,
    None,
    None
]

PRESET_FILE = "presets.json"


# ==========================================================
# DISPLAY AND RDS UPDATE SETTINGS
# ==========================================================

RSSI_UPDATE_MS = 500
RDS_UPDATE_MS = 100
DISPLAY_UPDATE_MS = 150

NOTIFICATION_DURATION_MS = 2000