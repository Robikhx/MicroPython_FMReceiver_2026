"""
============================================================
 Project: MicroPython FM Receiver 2026
 File: config.py

 Description:
 Central configuration file.
 Contains GPIO assignments, SPI/I2C parameters,
 radio frequencies, volume settings and encoder options.

 Author: MicroPython FM Receiver 2026 Team

 Implementation:
 Original project configuration.

============================================================
"""

# Si4703 tuner (I2C0)
I2C_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
TUNER_RESET_PIN = 6
TUNER_ADDRESS = 0x10
I2C_FREQUENCY = 100000

# Nokia 5110 display (SPI0)
SPI_ID = 0
SPI_SCK_PIN = 18
SPI_MOSI_PIN = 19
DISPLAY_DC_PIN = 20
DISPLAY_CS_PIN = 17
DISPLAY_RESET_PIN = 21
DISPLAY_BAUDRATE = 1000000
DISPLAY_CONTRAST = 0xB8
DISPLAY_ROTATE_180 = True

# KY-040 rotary encoder
ENCODER_CLK_PIN = 10
ENCODER_DT_PIN = 11
ENCODER_BUTTON_PIN = 12
ENCODER_DIRECTION = 1       # Change to -1 if rotation is reversed.
ENCODER_STEPS_PER_CLICK = 4
BUTTON_DEBOUNCE_MS = 35
DOUBLE_CLICK_MS = 350
LONG_PRESS_MS = 800

# FM radio settings
START_FREQUENCY = 990        # 99.0 MHz
MIN_FREQUENCY = 875          # 87.5 MHz
MAX_FREQUENCY = 1080         # 108.0 MHz
FREQUENCY_STEP = 1           # 0.1 MHz
START_VOLUME = 4              # 0-15
MIN_VOLUME = 0
MAX_VOLUME = 15

# Presets. Use None for an empty preset slot.
PRESETS = [875, 901, 995, 1025, None, None]
PRESET_FILE = "presets.json"

# Display / polling
RSSI_UPDATE_MS = 500
DISPLAY_UPDATE_MS = 150
