"""
============================================================
 Project: MicroPython FM Receiver 2026
 File: presets.py

 Description:
 Manages FM radio station presets.
 Supports saving, loading, updating and selecting
 stored frequencies.

 Author: MicroPython FM Receiver 2026 Team

 Implementation:
 Original implementation developed for this project.
 Uses MicroPython file handling for preset storage.

============================================================
"""

import json


class PresetManager:
    def __init__(self, filename, defaults):
        self.filename = filename
        self.presets = list(defaults)
        self.load()

    def load(self):
        try:
            with open(self.filename, "r") as file:
                saved = json.load(file)
            if isinstance(saved, list):
                self.presets = saved
        except (OSError, ValueError):
            # First run: use the defaults from config.py.
            self.save()

    def save(self):
        with open(self.filename, "w") as file:
            json.dump(self.presets, file)

    def set(self, index, frequency):
        self.presets[index] = int(frequency)
        self.save()

    def get(self, index):
        return self.presets[index]

    def next_valid(self, current_index, direction):
        """Find the next non-empty preset slot."""
        count = len(self.presets)
        for step in range(1, count + 1):
            index = (current_index + direction * step) % count
            if self.presets[index] is not None:
                return index
        return current_index
