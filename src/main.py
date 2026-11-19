"""
============================================================
Project: MicroPython FM Receiver 2026
File: main.py

Description:
Main application of the FM Receiver.
Initializes hardware components and coordinates
the tuner, display, rotary encoder, RDS and presets.

Author: MicroPython FM Receiver 2026 Team

Implementation:
Original application logic and system integration.

Technical References:
- MicroPython Documentation
- Silicon Labs Si4703 Datasheet
- Silicon Labs AN230 Programming Guide
============================================================
"""

import time
import config

from si4703 import Si4703
from nokia5110 import Nokia5110
from rotary_encoder import RotaryEncoder
from presets import PresetManager


class FMRadio:

    def __init__(self):

        # --------------------------------------------------
        # Initialize FM tuner
        # --------------------------------------------------

        self.tuner = Si4703(
            config.I2C_SDA_PIN,
            config.I2C_SCL_PIN,
            config.TUNER_RESET_PIN,
            config.I2C_ID,
            config.I2C_FREQUENCY,
            config.TUNER_ADDRESS
        )

        # --------------------------------------------------
        # Initialize display
        # --------------------------------------------------

        self.display = Nokia5110(
            config.SPI_ID,
            config.SPI_SCK_PIN,
            config.SPI_MOSI_PIN,
            config.DISPLAY_DC_PIN,
            config.DISPLAY_CS_PIN,
            config.DISPLAY_RESET_PIN,
            config.DISPLAY_BAUDRATE,
            config.DISPLAY_CONTRAST,
            config.DISPLAY_ROTATE_180
        )

        # --------------------------------------------------
        # Initialize rotary encoder
        # --------------------------------------------------

        self.encoder = RotaryEncoder(
            config.ENCODER_CLK_PIN,
            config.ENCODER_DT_PIN,
            config.ENCODER_BUTTON_PIN,
            config.ENCODER_DIRECTION,
            config.ENCODER_STEPS_PER_CLICK,
            config.BUTTON_DEBOUNCE_MS,
            config.DOUBLE_CLICK_MS,
            config.LONG_PRESS_MS
        )

        # --------------------------------------------------
        # Initialize presets
        # --------------------------------------------------

        self.presets = PresetManager(
            config.PRESET_FILE,
            config.PRESETS
        )

        # --------------------------------------------------
        # Radio state
        # --------------------------------------------------

        self.frequency = config.START_FREQUENCY
        self.volume = config.START_VOLUME

        self.mode = "RADIO"

        self.muted = False

        self.preset_index = 0

        # --------------------------------------------------
        # Radio signal information
        # --------------------------------------------------

        self.rssi = 0

        self.last_rssi_update = 0
        self.last_rds_update = 0
        self.last_display_update = 0

        # --------------------------------------------------
        # RDS information
        # --------------------------------------------------

        self.station = "--------"
        self.radiotext = ""

        self.ps_buffer = [" "] * 8
        self.rt_buffer = [" "] * 64

        self.rt_ab = None

        # --------------------------------------------------
        # Temporary notification
        # --------------------------------------------------

        self.message = None
        self.message_until = 0

        # --------------------------------------------------
        # Start tuner
        # --------------------------------------------------

        self.tuner.set_volume(self.volume)
        self.tuner.set_mute(False)

        self.frequency = self.tuner.set_frequency(
            self.frequency
        )

        self.update_display(force=True)

    # ======================================================
    # RADIO CONTROL
    # ======================================================

    # ------------------------------------------------------
    # Change frequency.
    # ------------------------------------------------------

    def change_frequency(self, amount):

        new_frequency = (
            self.frequency +
            amount * config.FREQUENCY_STEP
        )

        new_frequency = max(
            config.MIN_FREQUENCY,
            min(config.MAX_FREQUENCY, new_frequency)
        )

        if new_frequency != self.frequency:

            self.frequency = self.tuner.set_frequency(
                new_frequency
            )

            self.update_display(force=True)

    # ------------------------------------------------------
    # Change volume.
    # ------------------------------------------------------

    def change_volume(self, amount):

        self.volume += amount

        self.volume = max(
            config.MIN_VOLUME,
            min(config.MAX_VOLUME, self.volume)
        )

        self.tuner.set_volume(self.volume)

        self.show_notification(
            "VOLUME: {}".format(self.volume)
        )

    # ------------------------------------------------------
    # Change preset slot.
    # Empty slots can also be selected.
    # ------------------------------------------------------

    def change_preset(self, direction):

        count = self.presets.count()

        if count == 0:
            return

        self.preset_index = (
            self.preset_index + direction
        ) % count

        frequency = self.presets.get(self.preset_index)

        # Tune only if the selected slot is not empty.
        if frequency is not None:

            self.frequency = self.tuner.set_frequency(
                frequency
            )

        self.update_display(force=True)

    # ------------------------------------------------------
    # Save current frequency in selected preset.
    # ------------------------------------------------------

    def save_preset(self):

        self.presets.set(
            self.preset_index,
            self.frequency
        )

    # ======================================================
    # NOTIFICATIONS
    # ======================================================

    # ------------------------------------------------------
    # Show a message for a limited time.
    # ------------------------------------------------------

    def show_notification(self, message):

        self.message = message

        self.message_until = time.ticks_add(
            time.ticks_ms(),
            config.NOTIFICATION_DURATION_MS
        )

        self.display.show_message(message)

        self.last_display_update = time.ticks_ms()

    # ======================================================
    # ENCODER CONTROL
    # ======================================================

    def handle_encoder(self):

        for event, value in self.encoder.update():

            # ----------------------------------------------
            # Rotation
            # ----------------------------------------------

            if event == "ROTATE":

                if self.mode == "VOLUME":

                    self.change_volume(value)

                elif self.mode == "PRESET":

                    self.change_preset(value)

                else:

                    self.change_frequency(value)

            # ----------------------------------------------
            # Single click
            # ----------------------------------------------

            elif event == "SINGLE":

                if self.mode == "PRESET":

                    # Save current station in selected slot.
                    self.save_preset()

                    self.mode = "RADIO"

                    self.show_notification(
                        "SAVED P{}".format(self.preset_index + 1)
                    )

                elif self.mode == "VOLUME":

                    self.mode = "RADIO"

                    self.message = None

                    self.update_display(force=True)

                else:

                    self.mode = "VOLUME"

                    self.message = None

                    self.update_display(force=True)

            # ----------------------------------------------
            # Double click
            # ----------------------------------------------

            elif event == "DOUBLE":

                if self.mode == "PRESET":

                    self.mode = "RADIO"

                else:

                    self.mode = "PRESET"

                self.message = None

                self.update_display(force=True)

            # ----------------------------------------------
            # Long press
            # ----------------------------------------------

            elif event == "LONG":

                # Long press toggles mute only.
                self.muted = not self.muted

                self.tuner.set_mute(self.muted)

                if self.muted:

                    self.show_notification("MUTED")

                else:

                    self.show_notification("UNMUTED")

    # ======================================================
    # RDS DECODING
    # ======================================================

    # ------------------------------------------------------
    # Convert RDS character to readable ASCII.
    # ------------------------------------------------------

    def rds_char(self, value):

        if 32 <= value <= 126:

            return chr(value)

        return " "

    # ------------------------------------------------------
    # Decode RDS station name and RadioText.
    # ------------------------------------------------------

    def decode_rds(self):

        blocks = self.tuner.read_rds()

        if blocks is None:
            return

        block_a, block_b, block_c, block_d = blocks

        # RDS group type
        group = (block_b >> 12) & 0x0F

        # Version: 0 = A, 1 = B
        version_b = (block_b >> 11) & 1

        changed = False

        # --------------------------------------------------
        # GROUP 0A / 0B: PROGRAM SERVICE NAME (PS)
        # --------------------------------------------------

        if group == 0:

            segment = block_b & 0x03

            position = segment * 2

            self.ps_buffer[position] = self.rds_char(
                block_d >> 8
            )

            self.ps_buffer[position + 1] = self.rds_char(
                block_d & 0xFF
            )

            new_station = "".join(
                self.ps_buffer
            ).strip()

            if new_station and new_station != self.station:

                self.station = new_station

                changed = True

        # --------------------------------------------------
        # GROUP 2A / 2B: RADIOTEXT (RT)
        # --------------------------------------------------

        elif group == 2:

            # A/B flag
            ab_flag = (block_b >> 4) & 1

            # A/B changed: new RadioText message
            if self.rt_ab != ab_flag:

                self.rt_ab = ab_flag

                self.rt_buffer = [" "] * 64

                self.radiotext = ""

                changed = True

            segment = block_b & 0x0F

            if version_b == 0:

                # 2A: four characters per segment.
                position = segment * 4

                values = [
                    block_c >> 8,
                    block_c & 0xFF,
                    block_d >> 8,
                    block_d & 0xFF
                ]

            else:

                # 2B: two characters per segment.
                position = segment * 2

                values = [
                    block_d >> 8,
                    block_d & 0xFF
                ]

            # Store characters in the correct positions.
            for i, value in enumerate(values):

                index = position + i

                if index >= len(self.rt_buffer):
                    continue

                # 0x0D is the RadioText end marker.
                if value == 0x0D:

                    self.rt_buffer[index] = " "

                    for j in range(index + 1, len(self.rt_buffer)):
                        self.rt_buffer[j] = " "

                else:

                    self.rt_buffer[index] = self.rds_char(value)

            new_text = "".join(
                self.rt_buffer
            ).strip()

            if new_text != self.radiotext:

                self.radiotext = new_text

                changed = True

        # Refresh screen only when RDS data changes.
        if changed:

            self.update_display(force=True)

    # ======================================================
    # DISPLAY UPDATE
    # ======================================================

    def update_display(self, force=False):

        now = time.ticks_ms()

        if not force:

            if time.ticks_diff(
                now,
                self.last_display_update
            ) < config.DISPLAY_UPDATE_MS:

                return

        # Keep notification visible until timeout.
        if self.message is not None:

            if time.ticks_diff(
                self.message_until,
                now
            ) > 0:

                self.display.show_message(self.message)

                self.last_display_update = now

                return

            # Notification expired.
            self.message = None

        # Show normal radio interface.
        self.display.show_radio(
            self.frequency,
            self.volume,
            self.rssi,
            self.mode,
            self.muted,
            self.preset_index,
            self.station,
            self.radiotext
        )

        self.last_display_update = now

    # ======================================================
    # PERIODIC UPDATES
    # ======================================================

    def update_status(self):

        now = time.ticks_ms()

        # Update signal strength.
        if time.ticks_diff(
            now,
            self.last_rssi_update
        ) >= config.RSSI_UPDATE_MS:

            self.rssi = self.tuner.get_rssi()

            self.last_rssi_update = now

        # Read RDS information.
        if time.ticks_diff(
            now,
            self.last_rds_update
        ) >= config.RDS_UPDATE_MS:

            self.decode_rds()

            self.last_rds_update = now

        # Update display.
        self.update_display()

    # ======================================================
    # MAIN LOOP
    # ======================================================

    def run(self):

        print("FM Receiver started")

        while True:

            self.handle_encoder()

            self.update_status()

            time.sleep_ms(2)


# ==========================================================
# START APPLICATION
# ==========================================================

try:

    radio = FMRadio()

    radio.run()

except Exception as error:

    print("FM Receiver error:", repr(error))