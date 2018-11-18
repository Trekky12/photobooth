#!/usr/bin/env python3

from time import sleep
import sys
from shutil import copy2
import os
import logging


# Logging
logger = logging.getLogger("photobooth")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler( os.path.dirname(os.path.realpath(__file__)) + '/photobooth.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

try:
    import config
    from BoxIO import BoxIO
    from LEDs import LEDs
    from Camera import Camera
    
except ImportError as missing_module:
    print('--------------------------------------------')
    print('ERROR:')
    print(missing_module)
    print('')
    print(' - Please run the following command(s) to resolve:')
    if sys.version_info < (3,0):
        print('   pip install -r requirements.txt')
    else:
        print('   python3 -m pip install -r requirements.txt')
    print('')
    logger.error('%s', missing_module)
    sys.exit()


boxio = BoxIO(config)
leds = LEDs(0,0,config.pixel_count)
camera = Camera(config)


def exit_box():
    camera.stop()
    leds.clear()
    boxio.trigger_relay()
    boxio.cleanup()	 
    sys.exit()
    
    
def check_folders():
    folders_checked=[]
    folders_list=[config.images_folder]
    if hasattr(config, "images_folder_copy") and isinstance(config.images_folder_copy, list):
        folders_list.extend(config.images_folder_copy)    

    for folder in folders_list:
        if folder not in folders_checked:
            folders_checked.append(folder)
        else:
            print('ERROR: Cannot use same folder path ('+folder+') twice.')
            logger.error('ERROR: Cannot use same folder path (%s) twice.', folder)

        #Create folder if doesn't exist
        if not os.path.exists(folder):
            print('Creating folder: ' + folder)
            logger.info('Creating folder %s', folder)
            os.makedirs(folder)    

def main():

    # check folder existance
    check_folders()

    # intro screen
    intro_image = camera.get_path() + "/assets/intro.png"
    overlay_intro = camera.overlay_image(intro_image, 0, 4)

    i = 0
    while True:

        # LEDs rainbow
        leds.rainbow_step()
        
        # Blink the Dome LED
        i = i+1
        if i%config.blink_speed == 4:
            boxio.set_dome_led(True)
        elif i%config.blink_speed == 0:
            boxio.set_dome_led(False)
        
        # Dome button pressed
        if boxio.is_dome_pressed():
            print("Dome pressed")
            logger.info('Dome pressed')
            
            # disable buttons so no new interrupt rises
            boxio.disable_buttons()
            
            # remove intro overlay (only after first start because afterwards there is the last image as overlay)
            if overlay_intro is not None:
                camera.remove_overlay(overlay_intro)
                overlay_intro = None
            
            # create filename with timestamp
            camera.create_file_name() 

            # set image mode
            camera.set_image_mode_multi(boxio.is_image_mode_multi())
            
            # flash LEDs
            leds.show(255,255,255)
            
            # hide last image
            camera.hide_image()
            
            image_count = 1
            if boxio.is_image_mode_multi():
                image_count = config.image_count
            
            # capture 1/image_count images
            photo_filenames = []
            for photo_number in range(1, image_count + 1):
                    camera.prep_for_photo_screen(photo_number)
                    fname = camera.capture(photo_number)
                    photo_filenames.append(fname)
            
            # disable flash
            leds.clear()
            
            # do montage
            logger.info('Do montage')
            mfname = camera.convertMergeImages()
            # on a single shot without label the name is identical so skip this
            if not mfname in photo_filenames:
                photo_filenames.append(mfname)

            # show montage
            camera.show_image()
            
            # save photos into backup folder
            if hasattr(config, "images_folder_copy") and isinstance(config.images_folder_copy, list):
                for dest in config.images_folder_copy:
                    for src in photo_filenames:
                        print(src + ' -> ' + dest)
                        logger.info('Copy %s -> %s', src, dest)
                        copy2(src, dest)
            
            
            # enable buttons
            boxio.reset_dome_pressed()
            boxio.enable_buttons()
            
        if boxio.is_print_pressed():
            print("Print pressed")
            logger.info('Print pressed')
            boxio.reset_print_pressed()
            filename = camera.get_image()
            if filename is not None:
                boxio.printPic(filename)
            
        if boxio.is_exit_pressed():
            print("Exit pressed")
            logger.info('Exit pressed')
            raise Exception('Exit Button pressed')

        sleep(0.1)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        logger.info('Killed by Keyboard')
        print("Goodbye")

    except Exception as exception:
        logger.error('unexpected error: %s', exception)
        print("unexpected error: ", str(exception))

    finally:
        exit_box()
         