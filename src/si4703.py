"""
============================================================
Project: MicroPython FM Receiver 2026
File: si4703.py

Description:
Custom MicroPython driver for the Si4703 FM tuner.
Handles I2C communication, initialization, frequency
tuning, volume, mute, RSSI and RDS register reading.

Author: MicroPython FM Receiver 2026 Team

Implementation:
Original implementation developed for this project.

Technical References:
- Silicon Labs Si4703 Datasheet
- Silicon Labs AN230 Programming Guide
- SparkFun Si4703 Arduino Library:
  https://github.com/sparkfun/SparkFun_Si4703_Arduino_Library
============================================================
"""

from machine import Pin, I2C
import time


class Si4703:

    ADDRESS = 0x10

    def __init__(self, sda_pin, scl_pin, reset_pin,
                 i2c_id=0, i2c_frequency=100000,
                 address=0x10):

        self.address = address

        self.registers = [0] * 16

        self.volume = 4
        self.muted = False

        # Reset sequence
        reset = Pin(reset_pin, Pin.OUT, value=0)
        sda = Pin(sda_pin, Pin.OUT, value=0)

        time.sleep_ms(100)

        reset.value(1)

        time.sleep_ms(10)

        sda.init(Pin.IN)

        time.sleep_ms(10)

        # Initialize I2C
        self.i2c = I2C(
            i2c_id,
            sda=Pin(sda_pin),
            scl=Pin(scl_pin),
            freq=i2c_frequency
        )

        # Check tuner connection
        if self.address not in self.i2c.scan():

            raise OSError("Si4703 not found at I2C address 0x10")

        self.read_registers()

        # Enable internal oscillator
        self.registers[0x07] = 0x8100

        self.write_registers()

        time.sleep_ms(500)

        # Enable receiver
        self.registers[0x02] = 0x4001

        self.write_registers()

        time.sleep_ms(110)

        self.read_registers()

        # Enable RDS and 50 us de-emphasis
        self.registers[0x04] |= (1 << 12) | (1 << 11)

        # Configure channel spacing
        self.registers[0x05] &= ~0x00FF

        # 100 kHz channel spacing
        self.registers[0x05] |= (1 << 4)

        # Initial volume
        self.registers[0x05] |= self.volume

        self.write_registers()

    # ------------------------------------------------------
    # Read all 16 Si4703 registers.
    # ------------------------------------------------------

    def read_registers(self):

        data = self.i2c.readfrom(self.address, 32)

        for index in range(16):

            address = (0x0A + index) & 0x0F

            self.registers[address] = (
                (data[2 * index] << 8) |
                data[2 * index + 1]
            )

    # ------------------------------------------------------
    # Write registers 0x02 through 0x07.
    # ------------------------------------------------------

    def write_registers(self):

        data = bytearray(12)

        for index in range(6):

            value = self.registers[0x02 + index]

            data[2 * index] = (value >> 8) & 0xFF
            data[2 * index + 1] = value & 0xFF

        self.i2c.writeto(self.address, data)

    # ------------------------------------------------------
    # Wait for the STC (Seek/Tune Complete) flag.
    # ------------------------------------------------------

    def wait_for_stc(self, expected, timeout_ms=1500):

        start = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:

            self.read_registers()

            stc = bool(self.registers[0x0A] & (1 << 14))

            if stc == expected:
                return

            time.sleep_ms(10)

        raise OSError("Si4703 tuning timeout")

    # ------------------------------------------------------
    # Set FM frequency.
    # Frequency is expressed in 0.1 MHz units.
    # Example: 995 = 99.5 MHz.
    # ------------------------------------------------------

    def set_frequency(self, frequency):

        if frequency < 875 or frequency > 1080:

            raise ValueError("Frequency must be between 87.5 and 108.0 MHz")

        channel = frequency - 875

        self.read_registers()

        self.registers[0x03] &= ~((1 << 15) | 0x03FF)

        self.registers[0x03] |= channel

        # Start tuning
        self.registers[0x03] |= 1 << 15

        self.write_registers()

        try:
            self.wait_for_stc(True)

        finally:

            # Stop tuning
            self.registers[0x03] &= ~(1 << 15)

            self.write_registers()

        self.wait_for_stc(False)

        self.read_registers()

        return 875 + (self.registers[0x0B] & 0x03FF)

    # ------------------------------------------------------
    # Set volume from 0 to 15.
    # ------------------------------------------------------

    def set_volume(self, volume):

        volume = max(0, min(15, int(volume)))

        self.volume = volume

        self.read_registers()

        self.registers[0x05] = (
            (self.registers[0x05] & ~0x000F) |
            volume
        )

        self.write_registers()

    # ------------------------------------------------------
    # Enable or disable audio mute.
    # ------------------------------------------------------

    def set_mute(self, mute):

        self.muted = bool(mute)

        self.read_registers()

        if self.muted:

            # DMUTE = 0
            self.registers[0x02] &= ~(1 << 14)

        else:

            # DMUTE = 1
            self.registers[0x02] |= (1 << 14)

        self.write_registers()

    # ------------------------------------------------------
    # Read signal strength.
    # ------------------------------------------------------

    def get_rssi(self):

        self.read_registers()

        return self.registers[0x0A] & 0x00FF

    # ------------------------------------------------------
    # Read RDS data blocks A, B, C and D.
    # Returns None when no new RDS group is available.
    # ------------------------------------------------------

    def read_rds(self):

        self.read_registers()

        # RDSR = bit 15 of STATUSRSSI
        if not (self.registers[0x0A] & (1 << 15)):

            return None

        return (
            self.registers[0x0C],
            self.registers[0x0D],
            self.registers[0x0E],
            self.registers[0x0F]
        )