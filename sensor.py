import smbus2
import time

class SEN0460:
    # Define constants for selecting different particle measurement types
    PARTICLE_PM1_0_STANDARD   = 0x05
    PARTICLE_PM2_5_STANDARD   = 0x07
    PARTICLE_PM10_STANDARD    = 0x09
    PARTICLE_PM1_0_ATMOSPHERE = 0x0B
    PARTICLE_PM2_5_ATMOSPHERE = 0x0D
    PARTICLE_PM10_ATMOSPHERE  = 0x0F
    PARTICLENUM_0_3_UM_EVERY0_1L_AIR = 0x11
    PARTICLENUM_0_5_UM_EVERY0_1L_AIR = 0x13
    PARTICLENUM_1_0_UM_EVERY0_1L_AIR = 0x15
    PARTICLENUM_2_5_UM_EVERY0_1L_AIR = 0x17
    PARTICLENUM_5_0_UM_EVERY0_1L_AIR = 0x19
    PARTICLENUM_10_UM_EVERY0_1L_AIR  = 0x1B
    PARTICLENUM_GAIN_VERSION = 0x1D

    def __init__(self, bus=1, addr=0x19):
        """Initialize the sensor with the I2C bus and address."""
        self.bus = smbus2.SMBus(bus)
        self.addr = addr

    def gain_particle_concentration_ugm3(self, PMtype):
        """Get the particle concentration in µg/m³ for a specified PM type."""
        try:
            data = self.bus.read_i2c_block_data(self.addr, PMtype, 2)
            return (data[0] << 8) | data[1]
        except:
            return None

    def gain_all_concentrations(self):
        """Get all PM concentrations."""
        pm1 = self.gain_particle_concentration_ugm3(self.PARTICLE_PM1_0_STANDARD)
        pm25 = self.gain_particle_concentration_ugm3(self.PARTICLE_PM2_5_STANDARD)
        pm10 = self.gain_particle_concentration_ugm3(self.PARTICLE_PM10_STANDARD)
        return {'pm1': pm1, 'pm25': pm25, 'pm10': pm10}

    def gain_particle_counts(self):
        """Get particle counts for different sizes."""
        counts = {}
        sizes = [
            ('0_3_um', self.PARTICLENUM_0_3_UM_EVERY0_1L_AIR),
            ('0_5_um', self.PARTICLENUM_0_5_UM_EVERY0_1L_AIR),
            ('1_0_um', self.PARTICLENUM_1_0_UM_EVERY0_1L_AIR),
            ('2_5_um', self.PARTICLENUM_2_5_UM_EVERY0_1L_AIR),
            ('5_0_um', self.PARTICLENUM_5_0_UM_EVERY0_1L_AIR),
            ('10_um', self.PARTICLENUM_10_UM_EVERY0_1L_AIR),
        ]
        for name, reg in sizes:
            counts[name] = self.gain_particlenum_every0_1l(reg)
        return counts

    def gain_particlenum_every0_1l(self, PMtype):
        """Get the particle count per 0.1L of air for a specified PM type."""
        try:
            data = self.bus.read_i2c_block_data(self.addr, PMtype, 2)
            return (data[0] << 8) | data[1]
        except:
            return None

    def gain_version(self):
        """Get the sensor's firmware version."""
        try:
            data = self.bus.read_i2c_block_data(self.addr, self.PARTICLENUM_GAIN_VERSION, 1)
            return data[0]
        except:
            return None

    def set_lowpower(self):
        """Set the sensor to low power mode."""
        try:
            self.bus.write_i2c_block_data(self.addr, 0x01, [0x01])
        except:
            pass

    def awake(self):
        """Wake up the sensor from low power mode."""
        try:
            self.bus.write_i2c_block_data(self.addr, 0x01, [0x02])
        except:
            pass

def calculate_aqi(pm25):
    """Calculate AQI from PM2.5 concentration (approximate for real-time)."""
    breakpoints = [
        (0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]
    for low, high, aqi_low, aqi_high in breakpoints:
        if low <= pm25 <= high:
            return int(((aqi_high - aqi_low) / (high - low)) * (pm25 - low) + aqi_low)
    return 500  # max

if __name__ == "__main__":
    sensor = SEN0460()
    while True:
        sensor.awake()
        time.sleep(1)
        pm25 = sensor.gain_particle_concentration_ugm3(SEN0460.PARTICLE_PM2_5_STANDARD)
        if pm25 is not None:
            aqi = calculate_aqi(pm25)
            print(f"PM2.5: {pm25} µg/m³, AQI: {aqi}")
        else:
            print("Failed to read sensor")
        sensor.set_lowpower()
        time.sleep(5)