# import spidev
#
# class Touch:
#     def __init__(self, bus=1, device=0):
#         self.spi = spidev.SpiDev()
#         self.spi.open(bus, device)
#         self.spi.max_speed_hz = 1000000
#
#     def get_touch(self):
#         # 0x90 = Y-position, 0xD0 = X-position
#         y_raw = self.spi.xfer2([0x90, 0, 0])
#         y = ((y_raw[1] << 8) | y_raw[2]) >> 3
#
#         x_raw = self.spi.xfer2([0xD0, 0, 0])
#         x = ((x_raw[1] << 8) | x_raw[2]) >> 3
#
#         if x > 100 and y > 100: # Filter out "noise"
#             return x, y
#         return None
import spidev

class Touch:
    def __init__(self, bus=1, device=0, width=320, height=240):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = 1000000

        # display size
        self.width = width
        self.height = height

        # calibration values (adjust if needed)
        self.x_min = 0
        self.x_max = 3850
        self.y_min = 0
        self.y_max = 3800
    
    def scale(self, x, y):
        # 1. Subtract the 'hover' baseline (approx 100) 
        # to force the edge to actually be 0
        x_adj = x - 100 
        y_adj = y - 100

        # 2. Normalize using the adjusted range
        # (3850 - 100 = 3750)
        x_n = x_adj / 3750
        y_n = y_adj / 3700

        # 3. CRITICAL: Clamp to 0.0 - 1.0 
        # This removes the 'hovering 80+' issue entirely
        x_n = max(0, min(1, x_n))
        y_n = max(0, min(1, y_n))

        # 4. Map to your Landscape Orientation
        # Flip/Swap to match your top-left origin
        screen_x = int((1 - y_n) * (self.width - 1))
        screen_y = int((1 - x_n) * (self.height - 1))

        return screen_x, screen_y

     
     

    def get_touch(self):
        # 0x90 = Y-position, 0xD0 = X-position
        y_raw = self.spi.xfer2([0x90, 0, 0])
        y = ((y_raw[1] << 8) | y_raw[2]) >> 3
        
        x_raw = self.spi.xfer2([0xD0, 0, 0])
        x = ((x_raw[1] << 8) | x_raw[2]) >> 3
        
        if x > 100 and y > 100:  # Filter noise
            return self.scale(x, y)

        return None
