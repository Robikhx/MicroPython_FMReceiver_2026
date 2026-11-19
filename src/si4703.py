"""Simple Si4703 FM tuner driver for Raspberry Pi Pico / MicroPython."""

from machine import Pin, I2C
import time


class Si4703:
    ADDRESS = 0x10

    def __init__(self, sda_pin, scl_pin, reset_pin, i2c_id=0,
                 i2c_frequency=100000, address=0x10):
        self.address = address
        self.registers = [0] * 16
        self.volume = 4
        self.muted = False

        # Si4703 reset sequence. SDA is held LOW while RESET is LOW.
        reset = Pin(reset_pin, Pin.OUT, value=0)
        sda = Pin(sda_pin, Pin.OUT, value=0)
        time.sleep_ms(100)
        reset.value(1)
        time.sleep_ms(10)
        sda.init(Pin.IN)
        time.sleep_ms(10)

        self.i2c = I2C(i2c_id, sda=Pin(sda_pin), scl=Pin(scl_pin),
                       freq=i2c_frequency)

        if self.address not in self.i2c.scan():
            raise OSError("Si4703 not found at I2C address 0x10")

        self.read_registers()

        # Enable the Si4703 internal oscillator.
        self.registers[0x07] = 0x8100
        self.write_registers()
        time.sleep_ms(500)

        # Enable the receiver.
        self.registers[0x02] = 0x4001
        self.write_registers()
        time.sleep_ms(110)
        self.read_registers()

        # Enable RDS and configure 50 us de-emphasis.
        # RDS text decoding is intentionally not implemented here.
        self.registers[0x04] |= (1 << 12) | (1 << 11)

        # 100 kHz channel spacing; set initial volume.
        self.registers[0x05] &= ~0x00FF
        self.registers[0x05] |= (1 << 4) | (self.volume & 0x0F)
        self.write_registers()

    def read_registers(self):
        """Read all 16 registers (Si4703 I2C read starts at register 0x0A)."""
        data = self.i2c.readfrom(self.address, 32)
        for index in range(16):
            address = (0x0A + index) & 0x0F
            self.registers[address] = (data[2 * index] << 8) | data[2 * index + 1]

    def write_registers(self):
        """Write registers 0x02 through 0x07."""
        data = bytearray(12)
        for index in range(6):
            value = self.registers[0x02 + index]
            data[2 * index] = (value >> 8) & 0xFF
            data[2 * index + 1] = value & 0xFF
        self.i2c.writeto(self.address, data)

    def wait_for_stc(self, expected, timeout_ms=1500):
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            self.read_registers()
            stc = bool(self.registers[0x0A] & (1 << 14))
            if stc == expected:
                return
            time.sleep_ms(10)
        raise OSError("Si4703 tuning timeout")

    def set_frequency(self, frequency):
        """Tune to a frequency in 0.1 MHz units, e.g. 995 = 99.5 MHz."""
        if frequency < 875 or frequency > 1080:
            raise ValueError("Frequency must be between 87.5 and 108.0 MHz")

        channel = frequency - 875
        self.read_registers()
        self.registers[0x03] &= ~((1 << 15) | 0x03FF)
        self.registers[0x03] |= channel
        self.registers[0x03] |= 1 << 15
        self.write_registers()

        try:
            self.wait_for_stc(True)
        finally:
            self.registers[0x03] &= ~(1 << 15)
            self.write_registers()

        self.wait_for_stc(False)
        self.read_registers()
        return 875 + (self.registers[0x0B] & 0x03FF)

    def set_volume(self, volume):
        """Set hardware volume from 0 (quietest) to 15 (loudest)."""
        volume = max(0, min(15, int(volume)))
        self.volume = volume
        self.read_registers()
        self.registers[0x05] = (self.registers[0x05] & ~0x000F) | volume
        self.write_registers()

    def set_mute(self, mute):
        """Mute/unmute the tuner using the POWERCFG DMUTE bit."""
        self.muted = bool(mute)
        self.read_registers()
        if self.muted:
            self.registers[0x02] &= ~(1 << 14)  # DMUTE = 0
        else:
            self.registers[0x02] |= (1 << 14)   # DMUTE = 1
        self.write_registers()

    def get_rssi(self):
        self.read_registers()
        return self.registers[0x0A] & 0x00FF
