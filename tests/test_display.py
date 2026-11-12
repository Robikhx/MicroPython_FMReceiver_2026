# EXPECTED OUTPUT: 

# KY-040 Encoder Test
#Rotate or press the encoder.
#-----------------------------
#Clockwise | Counter: 1
#Clockwise | Counter: 2
#Counterclockwise | Counter: 1
#BUTTON PRESSED!


from machine import Pin, SPI
import framebuf
import time

# Nokia 5110 pinout
CE = 17
CLK = 18
DIN = 19
DC = 20
RST = 21

WIDTH = 84
HEIGHT = 48
CONTRAST = 0xB8

# SPI initialization
spi = SPI(
    0,
    baudrate=1000000,
    polarity=0,
    phase=0,
    sck=Pin(CLK),
    mosi=Pin(DIN)
)

cs = Pin(CE, Pin.OUT, value=1)
dc = Pin(DC, Pin.OUT)
rst = Pin(RST, Pin.OUT)

buffer = bytearray(WIDTH * HEIGHT // 8)

fb = framebuf.FrameBuffer(
    buffer, WIDTH, HEIGHT, framebuf.MONO_VLSB
)


def command(value):
    dc.value(0)
    cs.value(0)
    spi.write(bytes([value]))
    cs.value(1)


def update():
    # Rotate framebuffer 180 degrees
    rotated = bytearray(WIDTH * HEIGHT // 8)

    for x in range(WIDTH):
        for y in range(HEIGHT):
            if fb.pixel(x, y):
                index = ((HEIGHT - 1 - y) // 8) * WIDTH + (WIDTH - 1 - x)
                rotated[index] |= 1 << ((HEIGHT - 1 - y) % 8)

    command(0x40)
    command(0x80)

    dc.value(1)
    cs.value(0)
    spi.write(rotated)
    cs.value(1)


def initialize():
    rst.value(0)
    time.sleep_ms(20)
    rst.value(1)
    time.sleep_ms(20)

    command(0x21)
    command(CONTRAST)
    command(0x04)
    command(0x14)
    command(0x20)
    command(0x0C)

    fb.fill(0)
    update()


def test_display():
    print("Nokia 5110 Display Test - 180 Degree Rotation")

    initialize()
    print("Display initialized!")

    # Test 1: Clear screen
    print("Test 1: Clear screen")
    fb.fill(0)
    update()
    time.sleep(2)

    # Test 2: Full screen
    print("Test 2: Full screen")
    fb.fill(1)
    update()
    time.sleep(2)

    # Test 3: Text
    print("Test 3: Text")
    fb.fill(0)
    fb.text("NOKIA 5110", 0, 0, 1)
    fb.text("DISPLAY", 0, 16, 1)
    fb.text("TEST OK!", 0, 32, 1)
    update()
    time.sleep(3)

    # Test 4: Graphics
    print("Test 4: Graphics")
    fb.fill(0)
    fb.rect(0, 0, 84, 48, 1)
    fb.rect(5, 5, 74, 38, 1)
    fb.line(0, 0, 83, 47, 1)
    fb.line(83, 0, 0, 47, 1)
    update()
    time.sleep(3)

    # Test 5: Pixel pattern
    print("Test 5: Pixel pattern")
    fb.fill(0)

    for x in range(0, WIDTH, 4):
        for y in range(0, HEIGHT, 4):
            fb.pixel(x, y, 1)

    update()
    time.sleep(3)

    # Finish
    fb.fill(0)
    fb.text("ALL TESTS", 0, 8, 1)
    fb.text("PASSED!", 0, 24, 1)
    update()

    print("DISPLAY TEST PASSED!")


test_display()
