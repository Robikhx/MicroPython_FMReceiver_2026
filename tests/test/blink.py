#Si4703 FM Tuner Test
#-----------------------------
#I2C devices: ['0x10']
#Si4703 detected!
#Initializing tuner: OK
#Test 1: Frequency tuning
#Tuned frequency: 99.0 MHz
#Test 2: Signal strength
#RSSI: 35
#RSSI: 38
#RSSI: 37
#RSSI: 40
#RSSI: 39
#TUNER TEST COMPLETED!


from machine import Pin, I2C
import time

# Si4703 pinout
SDA = 4
SCL = 5
RST = 6

ADDRESS = 0x10

# Radio configuration
START_FREQ = 990       # 99.0 MHz
MIN_FREQ = 875         # 87.5 MHz
VOLUME = 2             # 0-15


class Si4703:

    def __init__(self):

        self.reg = [0] * 16

        # Hardware reset
        rst = Pin(RST, Pin.OUT, value=0)
        sda = Pin(SDA, Pin.OUT, value=0)

        time.sleep_ms(100)

        rst.value(1)
        time.sleep_ms(10)

        sda.init(Pin.IN)
        time.sleep_ms(10)

        # Initialize I2C
        self.i2c = I2C(
            0,
            sda=Pin(SDA),
            scl=Pin(SCL),
            freq=100000
        )

        devices = self.i2c.scan()

        print("I2C devices:", [hex(x) for x in devices])

        if ADDRESS not in devices:
            raise OSError("Si4703 not detected!")

        print("Si4703 detected!")

        self.read_registers()

        # Enable crystal oscillator
        self.reg[0x07] = 0x8100
        self.write_registers()

        time.sleep_ms(500)

        # Enable tuner and unmute
        self.reg[0x02] = 0x4001
        self.write_registers()

        time.sleep_ms(110)

        self.read_registers()

        # Configure RDS and de-emphasis
        self.reg[0x04] |= (1 << 12) | (1 << 11)

        # Configure 100 kHz spacing and volume
        self.reg[0x05] &= ~0x00FF
        self.reg[0x05] |= (1 << 4) | (VOLUME & 0x0F)

        self.write_registers()

    def read_registers(self):

        data = self.i2c.readfrom(ADDRESS, 32)

        for i in range(16):
            address = (0x0A + i) & 0x0F

            self.reg[address] = (
                (data[2 * i] << 8) |
                data[2 * i + 1]
            )

    def write_registers(self):

        data = bytearray(12)

        for i in range(6):
            value = self.reg[0x02 + i]

            data[2 * i] = (value >> 8) & 0xFF
            data[2 * i + 1] = value & 0xFF

        self.i2c.writeto(ADDRESS, data)

    def wait_stc(self, expected, timeout=1500):

        start = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start) < timeout:

            self.read_registers()

            stc = bool(self.reg[0x0A] & (1 << 14))

            if stc == expected:
                return

            time.sleep_ms(10)

        raise OSError("Tuning timeout!")

    def tune(self, frequency):

        if frequency < 875 or frequency > 1080:
            raise ValueError("Invalid frequency!")

        channel = frequency - MIN_FREQ

        self.read_registers()

        # Set channel and enable tuning
        self.reg[0x03] &= ~((1 << 15) | 0x03FF)
        self.reg[0x03] |= channel
        self.reg[0x03] |= 1 << 15

        self.write_registers()

        try:
            self.wait_stc(True)
        finally:
            self.reg[0x03] &= ~(1 << 15)
            self.write_registers()

        self.wait_stc(False)

        self.read_registers()

        actual = self.reg[0x0B] & 0x03FF

        return MIN_FREQ + actual

    def read_rssi(self):

        self.read_registers()

        return self.reg[0x0A] & 0xFF


def test_tuner():

    print("Si4703 FM Tuner Test")
    print("-----------------------------")

    tuner = Si4703()

    print("Initializing tuner: OK")

    # Test 1: Tune to 99.0 MHz
    print("\nTest 1: Frequency tuning")

    frequency = tuner.tune(START_FREQ)

    print(
        "Tuned frequency:",
        "{}.{} MHz".format(frequency // 10, frequency % 10)
    )

    # Test 2: Read signal strength
    print("\nTest 2: Signal strength")

    for i in range(5):

        rssi = tuner.read_rssi()

        print("RSSI:", rssi)

        time.sleep(1)

    print("\nTUNER TEST COMPLETED!")


try:
    test_tuner()

except Exception as error:
    print("\nTUNER TEST FAILED!")
    print("Error:", repr(error))
