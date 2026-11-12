# EXPECTED OUTPUT ON THE DISPLAY: 

# KY-040 Encoder Test
#Rotate or press the encoder.
#-----------------------------
#Clockwise | Counter: 1
#Clockwise | Counter: 2
#Counterclockwise | Counter: 1
#BUTTON PRESSED!

from machine import Pin
import time

# KY-040 pinout
CLK = 10
DT = 11
SW = 12

TRANSITIONS = (
    0, -1, 1, 0,
    1, 0, 0, -1,
    -1, 0, 0, 1,
    0, 1, -1, 0
)

TRANSITIONS_PER_STEP = 4
DIRECTION = 1

clk = Pin(CLK, Pin.IN, Pin.PULL_UP)
dt = Pin(DT, Pin.IN, Pin.PULL_UP)
sw = Pin(SW, Pin.IN, Pin.PULL_UP)

previous = (clk.value() << 1) | dt.value()
accumulator = 0
counter = 0

raw_button = sw.value()
stable_button = raw_button
changed_at = time.ticks_ms()

print("KY-040 Encoder Test")
print("Rotate or press the encoder.")
print("-----------------------------")

while True:

    # Encoder rotation
    current = (clk.value() << 1) | dt.value()

    if current != previous:
        index = (previous << 2) | current

        accumulator += TRANSITIONS[index]
        previous = current

        if accumulator >= TRANSITIONS_PER_STEP:
            counter += DIRECTION
            accumulator = 0
            print("Clockwise | Counter:", counter)

        elif accumulator <= -TRANSITIONS_PER_STEP:
            counter -= DIRECTION
            accumulator = 0
            print("Counterclockwise | Counter:", counter)

    # Encoder button
    now = time.ticks_ms()
    reading = sw.value()

    if reading != raw_button:
        raw_button = reading
        changed_at = now

    if (
        reading != stable_button
        and time.ticks_diff(now, changed_at) >= 35
    ):
        stable_button = reading

        if stable_button == 0:
            print("BUTTON PRESSED!")

    time.sleep_ms(1)
