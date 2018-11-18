#!/usr/bin/env python3

import RPi.GPIO as GPIO
from time import sleep
import cups
import logging

logger = logging.getLogger("photobooth")

class BoxIO:

    btn_single = None     # pin that the 'take 1 photo' button is attached to
    btn_multi  = None     # pin that the 'take multiple photos' button is attached to
    btn_print  = None     # pin that the 'print photo' button is attached to
    btn_dome   = None     # pin that the big dome button is attachted to
    btn_exit   = None     # pin that the 'exit' button is attached to
    btn_relay  = None     # pin that triggers the relay

    led_single = None     # pin that the single led is attached to
    led_multi  = None     # pin that the multi led is attached to
    led_print  = None     # pin that the print led is attached to
    led_dome   = None     # pin that the big dome led is attached to
    
    relay      = None     # pin that the relay for enable the printer is connected
    
    btn_print_pressed   = False
    btn_dome_pressed    = False
    btn_exit_pressed    = False
    image_mode_multi    = False

    def __init__(self, config):
    
        logger.info("Init Buttons")
    
        if hasattr(config, "btn_single"):
            self.btn_single = config.btn_single
        if hasattr(config, "btn_multi"):
            self.btn_multi = config.btn_multi
        if hasattr(config, "btn_print"):
            self.btn_print = config.btn_print
        if hasattr(config, "btn_dome"):
            self.btn_dome = config.btn_dome
        if hasattr(config, "btn_exit"):
            self.btn_exit = config.btn_exit
        if hasattr(config, "btn_relay"):
            self.btn_relay = config.btn_relay
        if hasattr(config, "led_single"):
            self.led_single = config.led_single
        if hasattr(config, "led_multi"):
            self.led_multi = config.led_multi
        if hasattr(config, "led_print"):
            self.led_print = config.led_print
        if hasattr(config, "led_dome"):
            self.led_dome = config.led_dome
        if hasattr(config, "relay"):
            self.relay = config.relay
                
        GPIO.setmode(GPIO.BCM)
        
        if not self.btn_single is None:
            GPIO.setup(self.btn_single, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        if not self.btn_multi is None:    
            GPIO.setup(self.btn_multi,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        if not self.btn_print is None:
            GPIO.setup(self.btn_print,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        if not self.btn_exit is None:
            GPIO.setup(self.btn_exit,   GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        if not self.btn_dome is None:
            GPIO.setup(self.btn_dome,   GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        if not self.btn_relay is None:
            GPIO.setup(self.btn_relay,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        if not self.led_single is None:
            GPIO.setup(self.led_single, GPIO.OUT)
            GPIO.output(self.led_single, True)
            
        if not self.led_multi is None:
            GPIO.setup(self.led_multi,  GPIO.OUT)
            GPIO.output(self.led_multi, False)
            
        if not self.led_print is None:
            GPIO.setup(self.led_print,  GPIO.OUT)
            GPIO.output(self.led_print, False)
            
        if not self.led_dome is None:
            GPIO.setup(self.led_dome,   GPIO.OUT)
            
            
        # Start printer with relay
        # the printer is connected to NO which means HIGH is holding this state and LOW is closing the relay
        if not self.relay is None:
            GPIO.setup(self.relay, GPIO.OUT, initial=GPIO.HIGH)
            self.trigger_relay()

        self.enable_buttons()

    def enable_buttons(self):
        if not self.btn_single is None:
            GPIO.add_event_detect(self.btn_single,  GPIO.FALLING, callback=self.btn_single_press,   bouncetime=200)
            
        if not self.btn_multi is None:
            GPIO.add_event_detect(self.btn_multi,   GPIO.FALLING, callback=self.btn_multi_press,    bouncetime=200)
        
        if not self.btn_print is None:
            GPIO.add_event_detect(self.btn_print,   GPIO.FALLING, callback=self.btn_print_press,    bouncetime=200)
        
        if not self.btn_exit is None:
            GPIO.add_event_detect(self.btn_exit,    GPIO.FALLING, callback=self.btn_exit_press,     bouncetime=200)
        
        if not self.btn_dome is None:
            GPIO.add_event_detect(self.btn_dome,    GPIO.FALLING, callback=self.btn_dome_press,     bouncetime=200)
            
        if not self.btn_relay is None:
            GPIO.add_event_detect(self.btn_relay,   GPIO.FALLING, callback=self.btn_relay_press,    bouncetime=200)
    
    def disable_buttons(self):
        if not self.btn_single is None:
            GPIO.remove_event_detect(self.btn_single)
        
        if not self.btn_multi is None:
            GPIO.remove_event_detect(self.btn_multi)
        
        if not self.btn_print is None:
            GPIO.remove_event_detect(self.btn_print)
        
        if not self.btn_exit is None:
            GPIO.remove_event_detect(self.btn_exit)
        
        if not self.btn_dome is None:
            GPIO.remove_event_detect(self.btn_dome)  
        
        if not self.btn_relay is None:
            GPIO.remove_event_detect(self.btn_relay)  
        
    def btn_single_press(self, channel):
        print("Button Single pressed")
        logger.info("Button Single pressed")
        
        self.image_mode_multi = False
        
        if not self.led_single is None:
            GPIO.output(self.led_single, True)
            
        if not self.led_multi is None:
            GPIO.output(self.led_multi, False)
        

    def btn_multi_press(self, channel):
        print("Button Multi pressed")
        logger.info("Button Multi pressed")
        
        self.image_mode_multi = True
        
        if not self.led_single is None:
            GPIO.output(self.led_single, False)
        
        if not self.led_multi is None:
            GPIO.output(self.led_multi, True)

    def btn_print_press(self, channel):
        print("Button Print pressed") 
        logger.info("Button Print pressed")
        self.btn_print_pressed = True
        GPIO.output(self.led_print, True)
        
    def btn_exit_press(self, channel):
        print("Button Exit pressed")   
        logger.info("Button Exit pressed")        
        self.btn_exit_pressed = True    

    def btn_dome_press(self, channel):
        print("Button Dome pressed") 
        logger.info("Button Dome pressed")
        self.btn_dome_pressed  = True
        
    def btn_relay_press(self, channel):
        print("Button Relay pressed")
        logger.info("Button Relay pressed")
        self.trigger_relay()   
        
    def is_image_mode_multi(self):
        return self.image_mode_multi
        
    def is_dome_pressed(self):
        return self.btn_dome_pressed
        
    def reset_dome_pressed(self):
        self.btn_dome_pressed = False
        
    def is_print_pressed(self):
        return self.btn_print_pressed    

    def reset_print_pressed(self):
        self.btn_print_pressed = False        

    def is_exit_pressed(self):
        return self.btn_exit_pressed   

    def cleanup(self):
        GPIO.cleanup()
        
    def set_dome_led(self, state):
        if not self.led_dome is None:
            GPIO.output(self.led_dome, state)
            
    def trigger_relay(self):
        GPIO.output(self.relay, GPIO.LOW)
        sleep(2)
        GPIO.output(self.relay, GPIO.HIGH) 
            
    def printPic(self, fileName):
        """
        This function prints the image on the printers
        inspired by https://github.com/zoroloco/boothy/blob/master/pbooth.py
        and https://stackoverflow.com/a/39118346
        """
        print("Try to print %s" %(fileName))
        logger.info("Try to print %s", fileName)
        
        conn = cups.Connection()
        printers = conn.getPrinters()
        default_printer = conn.getDefault()
        cups.setUser('pi')
        
        # possible options:
        #   'fit-to-page':'True'
        #   'copies': '2'
        #   'scaling' : '100'
        print_id = conn.printFile(default_printer, fileName, 'photobooth', {})
        
        print("Print job successfully created.")
        logger.info("Print job successfully created")
        
        print(conn.getJobs().get(print_id, None))
        logger.debug(conn.getJobs().get(print_id, None))
        # Check if print job is done
        while conn.getJobs().get(print_id, None):
            # blink LED
            GPIO.output(self.led_print, False)
            sleep(1)
            GPIO.output(self.led_print, True)
            sleep(1)
            logger.debug(conn.getJobs().get(print_id, None))
            logger.debug(conn.getJobAttributes(print_id))
        
        # Disable printing LED
        GPIO.output(self.led_print, False)
       