#!/usr/bin/env python3

import RPi.GPIO as GPIO
from time import sleep
import cups
import logging

logger = logging.getLogger("photobooth")

class BoxIO:

    btn_single      = None     # pin that the 'take 1 photo' button is attached to
    btn_multi       = None     # pin that the 'take multiple photos' button is attached to
    btn_print       = None     # pin that the 'print photo' button is attached to
    btn_dome        = None     # pin that the big dome button is attachted to
    btn_exit        = None     # pin that the 'exit' button is attached to
    btn_relay       = None     # pin that triggers the relay
    btn_retry_print = None     # pin that starts the printer in cups when an error occured

    led_single  = None     # pin that the single led is attached to
    led_multi   = None     # pin that the multi led is attached to
    led_print   = None     # pin that the print led is attached to
    led_dome    = None     # pin that the big dome led is attached to
    
    relay       = None     # pin that the relay for enable the printer is connected
    
    btn_print_pressed       = False
    btn_dome_pressed        = False
    btn_exit_pressed        = False
    image_mode_multi        = False
    btn_retry_print_pressed = False
    
    btn_single_enabled      = False
    btn_multi_enabled       = False
    btn_print_enabled       = False
    btn_dome_enabled        = False
    btn_exit_enabled        = False
    btn_relay_enabled       = False
    btn_retry_print_enabled = False
    
    conn            = None
    default_printer = None
    print_job_id    = None
    document        = None

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
        if hasattr(config, "btn_retry_print"):
            self.btn_retry_print = config.btn_retry_print
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
            
        if not self.btn_retry_print is None:
            GPIO.setup(self.btn_retry_print,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
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

        self.conn = cups.Connection()
        self.default_printer = self.conn.getDefault()
        cups.setUser('pi')
        self.enable_printer()
        self.conn.cancelAllJobs(self.default_printer)
        
        self.enable_button_exit()
        self.enable_button_relay()
        self.enable_buttons()

    def enable_buttons(self, only_Front = False):
        self.enable_button_single()
        self.enable_button_multi()
        self.enable_button_print()
        self.enable_button_dome()
        
        if not only_Front:
            #self.enable_button_exit()
            #self.enable_button_relay()
            self.enable_button_retry_print()
    
    def enable_button_single(self):
        if not self.btn_single is None and not self.btn_single_enabled:
            GPIO.add_event_detect(self.btn_single,          GPIO.FALLING, callback=self.btn_single_press,       bouncetime=200)
            self.btn_single_enabled = True

    def enable_button_multi(self):
        if not self.btn_multi is None and not self.btn_multi_enabled:
            GPIO.add_event_detect(self.btn_multi,           GPIO.FALLING, callback=self.btn_multi_press,        bouncetime=200)
            self.btn_multi_enabled = True

    def enable_button_print(self):
        if not self.btn_print is None and not self.btn_print_enabled:
            GPIO.add_event_detect(self.btn_print,           GPIO.FALLING, callback=self.btn_print_press,        bouncetime=200)
            self.btn_print_enabled = True
            
    def enable_button_dome(self):
        if not self.btn_dome is None and not self.btn_dome_enabled:
            GPIO.add_event_detect(self.btn_dome,            GPIO.FALLING, callback=self.btn_dome_press,         bouncetime=200)
            self.btn_dome_enabled = True
            
    def enable_button_exit(self):
        if not self.btn_exit is None and not self.btn_exit_enabled:
            GPIO.add_event_detect(self.btn_exit,            GPIO.FALLING, callback=self.btn_exit_press,         bouncetime=200)
            self.btn_exit_enabled = True

    def enable_button_relay(self):
        if not self.btn_relay is None and not self.btn_relay_enabled:
            GPIO.add_event_detect(self.btn_relay,          GPIO.FALLING, callback=self.btn_relay_press,        bouncetime=200)
            self.btn_relay_enabled = True

    def enable_button_retry_print(self):
        if not self.btn_retry_print is None and not self.btn_retry_print_enabled:
            GPIO.add_event_detect(self.btn_retry_print,    GPIO.FALLING, callback=self.btn_retry_print_press,  bouncetime=200)
            self.btn_retry_print_enabled = True
    
    def disable_buttons(self, only_Front = False):
        self.disable_button_single()
        self.disable_button_multi()
        self.disable_button_print()
        self.disable_button_dome()
        
        if not only_Front:
            #self.disable_button_exit()
            #self.disable_button_relay()
            self.disable_button_retry_print()

    def disable_button_single(self):
        if not self.btn_single is None and self.btn_single_enabled:
            GPIO.remove_event_detect(self.btn_single)
            self.btn_single_enabled = False
            
    def disable_button_multi(self):
        if not self.btn_multi is None and self.btn_multi_enabled:
            GPIO.remove_event_detect(self.btn_multi)
            self.btn_multi_enabled = False

    def disable_button_print(self):
        if not self.btn_print is None and self.btn_print_enabled:
            GPIO.remove_event_detect(self.btn_print)
            self.btn_print_enabled = False
           
    def disable_button_dome(self):
        if not self.btn_dome is None and self.btn_dome_enabled:
            GPIO.remove_event_detect(self.btn_dome)
            self.btn_dome_enabled = False

    def disable_button_exit(self):
        if not self.btn_exit is None and self.btn_exit_enabled:
            GPIO.remove_event_detect(self.btn_exit)
            self.btn_exit_enabled = False

    def disable_button_relay(self):
        if not self.btn_relay is None and self.btn_relay_enabled:
            GPIO.remove_event_detect(self.btn_relay)
            self.btn_relay_enabled = False

    def disable_button_retry_print(self):
        if not self.btn_retry_print is None and self.btn_retry_print_enabled:
            GPIO.remove_event_detect(self.btn_retry_print)
            self.btn_retry_print_enabled = False
     
     
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
        self.set_print_led(True)
        
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
        
    def btn_retry_print_press(self, channel):
        print("Button Retry Print pressed")
        logger.info("Button Retry Print pressed")
        self.btn_retry_print_pressed = True
        
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

    def is_retry_print_pressed(self):
        return self.btn_retry_print_pressed    

    def reset_retry_print_pressed(self):
        self.btn_retry_print_pressed = False              

    def cleanup(self):
        GPIO.cleanup()
        
    def set_dome_led(self, state):
        if not self.led_dome is None:
            GPIO.output(self.led_dome, state)
            
    def set_print_led(self, state):
        if not self.led_print is None:
            GPIO.output(self.led_print, state)
            
    def trigger_relay(self):
        GPIO.output(self.relay, GPIO.LOW)
        sleep(2)
        GPIO.output(self.relay, GPIO.HIGH) 
            
    def print_image(self, filename):
        """
        This function prints the image on the printers
        inspired by https://github.com/zoroloco/boothy/blob/master/pbooth.py
        and https://stackoverflow.com/a/39118346
        """
        if filename is not None:
            self.document = filename
            print("Try to print %s" %(self.document))
            logger.info("Try to print %s", self.document)
            # possible options:
            #   'fit-to-page':'True'
            #   'copies': '2'
            #   'scaling' : '100'
            self.print_job_id = self.conn.printFile(self.default_printer, self.document, 'photobooth', {})
            
            print("Print job successfully created.")
            logger.info("Print job successfully created")
            
            return self.print_job_id

    def print_started(self):
        if self.print_job_id is None:
            return False
        return True

    # Check if print job is done
    def printed(self):
        #logger.info(self.conn.getJobs().get(self.print_job_id, None))
        if self.conn.getJobs().get(self.print_job_id, None):
            return False
        
        # Reset
        print("Job printed")
        logger.info("Job printed")
        self.print_job_id = None
        self.document = None
        return True

    # Check if print job is hold 
    def has_print_error(self):
        attr = self.conn.getPrinterAttributes(self.default_printer)

        if attr["printer-state"] == 5:
            return attr["printer-state-message"]
        
        if self.print_started() and not self.printed():
            job = self.conn.getJobAttributes(self.print_job_id)

            if job["job-state"] == 4 or job["job-state"] == 6:
                return job["job-printer-state-message"]

        return False
        
    def cancel_print_job(self, retry = False):
        print("Cancel/Restart Job")
        logger.info("Cancel/Restart Job")
        self.enable_printer()
        
        if self.print_started() and not self.printed():
            # Release of job is not supported so instead cancel and resubmit the job
            self.conn.cancelJob(self.print_job_id)
            
            if retry:
                self.print_image(self.document)
            else:
                self.print_job_id = None
                
    def enable_printer(self, retry = False):
        print("Enable Printer/Accept Jobs")
        logger.info("Enable Printer/Accept Jobs")
        self.conn.enablePrinter(self.default_printer)
        self.conn.acceptJobs(self.default_printer)