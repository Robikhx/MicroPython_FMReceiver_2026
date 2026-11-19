"""
============================================================
Project: MicroPython FM Receiver 2026
File: presets.py

Description:
Manages FM radio station presets.
Supports loading, saving, updating and selecting
stored frequencies.

Author: MicroPython FM Receiver 2026 Team

Implementation:
Original implementation developed for this project.
Uses MicroPython JSON and file handling.

Technical References:
- MicroPython JSON Documentation
- MicroPython File I/O Documentation
============================================================
"""

import json


class PresetManager:

    def __init__(self, filename, defaults):

        self.filename = filename
        self.presets = list(defaults)

        self.load()

    # ------------------------------------------------------
    # Load presets from file.
    # ------------------------------------------------------

    def load(self):

        try:

            with open(self.filename, "r") as file:

                saved = json.load(file)

            if isinstance(saved, list):

                # Keep the number of slots defined in config.py.
                if len(saved) == len(self.presets):

                    self.presets = saved

        except (OSError, ValueError):

            # First run: use default presets.
            self.save()

    # ------------------------------------------------------
    # Save presets to file.
    # ------------------------------------------------------

    def save(self):

        with open(self.filename, "w") as file:

            json.dump(self.presets, file)

    # ------------------------------------------------------
    # Save a frequency in a selected preset.
    # ------------------------------------------------------

    def set(self, index, frequency):

        if index < 0 or index >= len(self.presets):
            return

        self.presets[index] = int(frequency)

        self.save()

    # ------------------------------------------------------
    # Get a preset frequency.
    # Returns None if the slot is empty.
    # ------------------------------------------------------

    def get(self, index):

        if index < 0 or index >= len(self.presets):
            return None

        return self.presets[index]

    # ------------------------------------------------------
    # Return the number of preset slots.
    # ------------------------------------------------------

    def count(self):

        return len(self.presets)