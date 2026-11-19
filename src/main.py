"""Main application for the MicroPython FM receiver."""

import time
import config
from si4703 import Si4703
from nokia5110 import Nokia5110
from rotary_encoder import RotaryEncoder
from presets import PresetManager


class FMRadio:
    def __init__(self):
        # Create each hardware component.
        self.tuner = Si4703(
            config.I2C_SDA_PIN,
            config.I2C_SCL_PIN,
            config.TUNER_RESET_PIN,
            config.I2C_ID,
            config.I2C_FREQUENCY,
            config.TUNER_ADDRESS
        )

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

        self.presets = PresetManager(config.PRESET_FILE, config.PRESETS)

        self.frequency = config.START_FREQUENCY
        self.volume = config.START_VOLUME
        self.mode = "RADIO"       # RADIO, VOLUME or PRESET
        self.muted = False
        self.preset_index = 0
        self.rssi = 0
        self.last_rssi_update = 0
        self.last_display_update = 0

        self.tuner.set_volume(self.volume)
        self.tuner.set_mute(False)
        self.frequency = self.tuner.set_frequency(self.frequency)
        self.update_display(force=True)

    def change_frequency(self, amount):
        new_frequency = self.frequency + amount * config.FREQUENCY_STEP
        new_frequency = max(config.MIN_FREQUENCY,
                            min(config.MAX_FREQUENCY, new_frequency))

        if new_frequency != self.frequency:
            self.frequency = self.tuner.set_frequency(new_frequency)
            self.update_display(force=True)

    def change_volume(self, amount):
        self.volume += amount
        self.volume = max(config.MIN_VOLUME,
                          min(config.MAX_VOLUME, self.volume))
        self.tuner.set_volume(self.volume)
        self.update_display(force=True)

    def change_preset(self, direction):
        index = self.presets.next_valid(self.preset_index, direction)
        self.preset_index = index
        frequency = self.presets.get(index)
        if frequency is not None:
            self.frequency = self.tuner.set_frequency(frequency)
        self.update_display(force=True)

    def save_preset(self):
        self.presets.set(self.preset_index, self.frequency)
        self.update_display(force=True)

    def handle_encoder(self):
        for event, value in self.encoder.update():
            if event == "ROTATE":
                if self.mode == "VOLUME":
                    self.change_volume(value)
                elif self.mode == "PRESET":
                    self.change_preset(value)
                else:
                    self.change_frequency(value)

            elif event == "SINGLE":
                # One click: enter/leave volume mode.
                if self.mode == "VOLUME":
                    self.mode = "RADIO"
                elif self.mode == "PRESET":
                    self.mode = "RADIO"
                else:
                    self.mode = "VOLUME"
                self.update_display(force=True)

            elif event == "DOUBLE":
                # Double click: enter/leave station preset selection.
                if self.mode == "PRESET":
                    self.mode = "RADIO"
                else:
                    self.mode = "PRESET"
                self.update_display(force=True)

            elif event == "LONG":
                # Hold: mute/unmute. Save current station as the selected preset.
                self.muted = not self.muted
                self.tuner.set_mute(self.muted)
                # A long press also stores the current frequency in the slot.
                self.save_preset()

    def update_status(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_rssi_update) >= config.RSSI_UPDATE_MS:
            self.rssi = self.tuner.get_rssi()
            self.last_rssi_update = now

        if time.ticks_diff(now, self.last_display_update) >= config.DISPLAY_UPDATE_MS:
            self.update_display()

    def update_display(self, force=False):
        now = time.ticks_ms()
        if force or time.ticks_diff(now, self.last_display_update) >= config.DISPLAY_UPDATE_MS:
            self.display.show_radio(
                self.frequency,
                self.volume,
                self.rssi,
                self.mode,
                self.muted,
                self.preset_index
            )
            self.last_display_update = now

    def run(self):
        print("FM receiver started")
        while True:
            self.handle_encoder()
            self.update_status()
            time.sleep_ms(2)


# Start the radio.
try:
    radio = FMRadio()
    radio.run()
except Exception as error:
    print("FM receiver error:", repr(error))
