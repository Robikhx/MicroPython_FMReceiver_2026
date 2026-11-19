"""
============================================================
Project: MicroPython FM Receiver 2026
File: nokia5110.py

Description:
Custom driver for the Nokia 5110 LCD (PCD8544).
Handles SPI communication, display initialization,
framebuffer management and text rendering.

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

    def __init__(self, spi_id, sck_pin, mosi_pin, dc_pin,
                 cs_pin, reset_pin, baudrate=1000000,
                 contrast=0xB8, rotate_180=True):

        self.rotate_180 = rotate_180

        self.spi = SPI(
            spi_id,
            baudrate=baudrate,
            polarity=0,
            phase=0,
            sck=Pin(sck_pin),
            mosi=Pin(mosi_pin)
        )

        self.cs = Pin(cs_pin, Pin.OUT, value=1)
        self.dc = Pin(dc_pin, Pin.OUT, value=0)
        self.reset = Pin(reset_pin, Pin.OUT, value=1)

        self.buffer = bytearray(self.WIDTH * self.HEIGHT // 8)

        self.framebuffer = framebuf.FrameBuffer(
            self.buffer,
            self.WIDTH,
            self.HEIGHT,
            framebuf.MONO_VLSB
        )

        self.initialize(contrast)

    # ------------------------------------------------------
    # Send one command to the display.
    # ------------------------------------------------------

    def send_command(self, value):

        self.dc.value(0)
        self.cs.value(0)

        self.spi.write(bytes([value]))

        self.cs.value(1)

    # ------------------------------------------------------
    # Initialize the PCD8544 controller.
    # ------------------------------------------------------

    def initialize(self, contrast):

        self.reset.value(0)
        time.sleep_ms(20)

        self.reset.value(1)
        time.sleep_ms(20)

        self.send_command(0x21)
        self.send_command(contrast)
        self.send_command(0x04)
        self.send_command(0x14)
        self.send_command(0x20)
        self.send_command(0x0C)

        self.clear()

    # ------------------------------------------------------
    # Clear the screen.
    # ------------------------------------------------------

    def clear(self):

        self.framebuffer.fill(0)
        self.update()

    # ------------------------------------------------------
    # Send framebuffer data to the LCD.
    # ------------------------------------------------------

    def update(self):

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

        self.send_command(0x40)
        self.send_command(0x80)

        self.dc.value(1)
        self.cs.value(0)

        self.spi.write(output)

        self.cs.value(1)

    # ------------------------------------------------------
    # Display a temporary message.
    # Maximum 10 characters.
    # ------------------------------------------------------

    def show_message(self, message):

        fb = self.framebuffer

        fb.fill(0)

        message = str(message)[:10]

        x = max(0, (self.WIDTH - len(message) * 8) // 2)

        fb.text(message, x, 20, 1)

        self.update()

    # ------------------------------------------------------
    # Display the main radio interface.
    # ------------------------------------------------------

    def show_radio(self, frequency, volume, rssi, mode,
                   muted, preset_index=None,
                   station="--------", radiotext=""):

        fb = self.framebuffer

        fb.fill(0)

        # Header
        fb.text("FM RADIO", 0, 0, 1)
        fb.hline(0, 9, 84, 1)

        # Mute screen
        if muted:

            fb.text("MUTED", 20, 20, 1)

            self.update()
            return

        # Volume screen
        if mode == "VOLUME":

            fb.text("VOLUME: {}".format(volume), 0, 20, 1)

        # Preset screen
        elif mode == "PRESET":

            fb.text("PRESET", 0, 12, 1)

            if preset_index is not None:
                fb.text("P{}".format(preset_index + 1), 0, 28, 1)

            fb.text(
                "{}.{} MHz".format(
                    frequency // 10,
                    frequency % 10
                ),
                24, 28, 1
            )

        # Normal radio screen
        else:

            fb.text(
                "{}.{} MHz".format(
                    frequency // 10,
                    frequency % 10
                ),
                0, 12, 1
            )

            # RDS station name
            fb.text(str(station)[:8], 0, 24, 1)

            # RDS RadioText or RSSI if no text is available
            if radiotext:
                fb.text(str(radiotext)[:10], 0, 36, 1)
            else:
                fb.text("RSSI: {}".format(rssi), 0, 36, 1)

        self.update()