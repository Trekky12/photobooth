#!/usr/bin/env python3

import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI

class LEDs:

    rainbow_index = 0

    def __init__(self, SPI_PORT = 0, SPI_DEVICE = 0, PIXEL_COUNT = 14):
        self.pixels = Adafruit_WS2801.WS2801Pixels(PIXEL_COUNT, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
        self.clear()
        
    def clear(self):
        self.pixels.clear()
        self.pixels.show()
        
    def show(self, r, g, b):
        for i in range(self.pixels.count()):
            self.pixels.set_pixel_rgb(i, r, g, b)
        self.pixels.show()
        
    def wheel(self, pos):
        """
        Define the wheel function to interpolate between different hues.
        """
        if pos < 85:
            return Adafruit_WS2801.RGB_to_color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Adafruit_WS2801.RGB_to_color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Adafruit_WS2801.RGB_to_color(0, pos * 3, 255 - pos * 3)    

    """
    def rainbow_cycle(self):
        for j in range(256): # one cycle of all 256 colors in the wheel
            for i in range(self.pixels.count()):
                # tricky math! we use each pixel as a fraction of the full 96-color wheel
                # (thats the i / strip.numPixels() part)
                # Then add in j which makes the colors go around per pixel
                # the % 96 is to make the wheel cycle around
                self.pixels.set_pixel(i, self.wheel(((i * 256 // self.pixels.count()) + j) % 256) )
                self.pixels.show()        
    """
    def rainbow_step(self):
        for i in range(self.pixels.count()):
            self.pixels.set_pixel(i, self.wheel(((i * 256 // self.pixels.count()) + self.rainbow_index) % 256) )
        self.pixels.show()   
        
        self.rainbow_index += 1
        if self.rainbow_index >= 255:
            self.rainbow_index = 0
        