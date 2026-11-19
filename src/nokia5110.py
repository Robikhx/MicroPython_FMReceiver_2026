"""
============================================================
 Project: MicroPython FM Receiver 2026
 File: nokia5110.py

 Description:
 Custom driver for the Nokia 5110 LCD (PCD8544).
 Handles SPI communication, display initialization,
 framebuffer management, text and graphics rendering.

 Author: MicroPython FM Receiver 2026 Team

 Implementation:
 Original implementation developed for this project.

 Technical References:
 - Philips PCD8544 LCD Controller Datasheet
 - MicroPython FrameBuffer Documentation
 - McAuser MicroPython PCD8544:
   https://github.com/mcauser/micropython-pcd8544

============================================================
"""

from machine import Pin, SPI
import framebuf
import time


class Nokia5110:
    WIDTH = 84
    HEIGHT = 48

    def __init__(self, spi_id, sck_pin, mosi_pin, dc_pin, cs_pin,
                 reset_pin, baudrate=1000000, contrast=0xB8,
                 rotate_180=True):
        self.rotate_180 = rotate_180
        self.spi = SPI(spi_id, baudrate=baudrate, polarity=0, phase=0,
                       sck=Pin(sck_pin), mosi=Pin(mosi_pin))
        self.cs = Pin(cs_pin, Pin.OUT, value=1)
        self.dc = Pin(dc_pin, Pin.OUT, value=0)
        self.reset = Pin(reset_pin, Pin.OUT, value=1)

        self.buffer = bytearray(self.WIDTH * self.HEIGHT // 8)
        self.framebuffer = framebuf.FrameBuffer(
            self.buffer, self.WIDTH, self.HEIGHT, framebuf.MONO_VLSB)

        self.initialize(contrast)

    def send_command(self, value):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytes([value]))
        self.cs.value(1)

    def initialize(self, contrast):
        self.reset.value(0)
        time.sleep_ms(20)
        self.reset.value(1)
        time.sleep_ms(20)

        self.send_command(0x21)       # Extended instruction set
        self.send_command(contrast)   # LCD contrast
        self.send_command(0x04)       # Temperature coefficient
        self.send_command(0x14)       # Bias system
        self.send_command(0x20)       # Basic instruction set
        self.send_command(0x0C)       # Normal display mode
        self.clear()

    def clear(self):
        self.framebuffer.fill(0)
        self.update()

    def update(self):
        # The original display test showed that this module is mounted rotated.
        if self.rotate_180:
            rotated = bytearray(len(self.buffer))
            for x in range(self.WIDTH):
                for y in range(self.HEIGHT):
                    if self.framebuffer.pixel(x, y):
                        new_x = self.WIDTH - 1 - x
                        new_y = self.HEIGHT - 1 - y
                        index = (new_y // 8) * self.WIDTH + new_x
                        rotated[index] |= 1 << (new_y % 8)
            output = rotated
        else:
            output = self.buffer

        self.send_command(0x40)       # Y address = 0
        self.send_command(0x80)       # X address = 0
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(output)
        self.cs.value(1)

    def show_radio(self, frequency, volume, rssi, mode, muted, preset_index=None):
        """Draw the complete radio screen."""
        fb = self.framebuffer
        fb.fill(0)
        fb.text("FM RECEIVER", 0, 0, 1)
        fb.hline(0, 9, 84, 1)

        # Frequency e.g. 99.5 MHz
        frequency_text = "{}.{} MHz".format(frequency // 10, frequency % 10)
        fb.text(frequency_text, 0, 15, 1)

        if mode == "VOLUME":
            fb.text("VOLUME: {}".format(volume), 0, 27, 1)
        elif mode == "PRESET":
            fb.text("PRESET MODE", 0, 27, 1)
            if preset_index is not None:
                fb.text("SLOT: {}".format(preset_index + 1), 0, 37, 1)
        else:
            fb.text("RSSI: {}".format(rssi), 0, 27, 1)

        if muted:
            fb.text("MUTED", 48, 37, 1)
        else:
            fb.text("VOL {}".format(volume), 0, 37, 1)
            # Very simple signal bar (RSSI is a relative Si4703 value).
            bars = max(0, min(5, rssi // 10))
            for i in range(bars):
                fb.fill_rect(54 + i * 5, 44 - (i + 1) * 2, 3, (i + 1) * 2, 1)

        fb.hline(0, 46, 84, 1)
        self.update()
