"""
============================================================
 Project: MicroPython FM Receiver 2026
 File: rotary_encoder.py

 Description:
 Custom KY-040 rotary encoder driver.
 Handles rotation direction, button presses,
 debouncing, single clicks, double clicks and long presses.

 Author: MicroPython FM Receiver 2026 Team

 Implementation:
 Original implementation developed for this project.
 Uses quadrature decoding and software debouncing.

 Technical References:
 - KY-040 Rotary Encoder Datasheet
 - Mike Teachman MicroPython Rotary:
   https://github.com/miketeachman/micropython-rotary
 - MicroPython GPIO Documentation

============================================================
"""

from machine import Pin
import time


class RotaryEncoder:
    TRANSITIONS = (
        0, -1, 1, 0,
        1, 0, 0, -1,
        -1, 0, 0, 1,
        0, 1, -1, 0
    )

    def __init__(self, clk_pin, dt_pin, button_pin,
                 direction=1, steps_per_click=4,
                 debounce_ms=35, double_click_ms=350,
                 long_press_ms=800):
        self.clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self.dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
        self.button = Pin(button_pin, Pin.IN, Pin.PULL_UP)

        self.direction = direction
        self.steps_per_click = steps_per_click
        self.debounce_ms = debounce_ms
        self.double_click_ms = double_click_ms
        self.long_press_ms = long_press_ms

        self.previous_state = (self.clk.value() << 1) | self.dt.value()
        self.accumulator = 0

        self.raw_button = self.button.value()
        self.stable_button = self.raw_button
        self.button_changed_at = time.ticks_ms()
        self.press_started_at = 0
        self.long_press_sent = False
        self.pending_click_at = None

        self.rotation = 0
        self.events = []

    def update(self):
        """Read the encoder and add events: ROTATE, SINGLE, DOUBLE or LONG."""
        self._read_rotation()
        self._read_button()
        result = self.events
        self.events = []
        return result

    def _read_rotation(self):
        current = (self.clk.value() << 1) | self.dt.value()
        if current == self.previous_state:
            return

        index = (self.previous_state << 2) | current
        self.accumulator += self.TRANSITIONS[index]
        self.previous_state = current

        if self.accumulator >= self.steps_per_click:
            self.events.append(("ROTATE", self.direction))
            self.accumulator = 0
        elif self.accumulator <= -self.steps_per_click:
            self.events.append(("ROTATE", -self.direction))
            self.accumulator = 0

    def _read_button(self):
        now = time.ticks_ms()
        reading = self.button.value()

        # Restart debounce timer when raw input changes.
        if reading != self.raw_button:
            self.raw_button = reading
            self.button_changed_at = now

        # Accept a button state only after it is stable.
        if (reading != self.stable_button and
                time.ticks_diff(now, self.button_changed_at) >= self.debounce_ms):
            self.stable_button = reading
            if self.stable_button == 0:
                self.press_started_at = now
                self.long_press_sent = False

            else:
                if not self.long_press_sent:
                    if self.pending_click_at is None:
                        self.pending_click_at = now
                    elif time.ticks_diff(now, self.pending_click_at) <= self.double_click_ms:
                        self.events.append(("DOUBLE", 0))
                        self.pending_click_at = None

        # Long press fires once while the button is held.
        if self.stable_button == 0 and not self.long_press_sent:
            if time.ticks_diff(now, self.press_started_at) >= self.long_press_ms:
                self.events.append(("LONG", 0))
                self.long_press_sent = True
                self.pending_click_at = None

        # A single click is emitted only after the double-click window expires.
        if self.pending_click_at is not None:
            if time.ticks_diff(now, self.pending_click_at) > self.double_click_ms:
                self.events.append(("SINGLE", 0))
                self.pending_click_at = None
