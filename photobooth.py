#!/usr/bin/env python3

from time import sleep
import sys
import shutil
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

    # check folders for duplicates and create missing folders
    for folder in folders_list:
        if folder not in folders_checked:
            folders_checked.append(folder)
        else:
            print('ERROR: Cannot use same folder path ('+folder+') twice.')
            logger.error('ERROR: Cannot use same folder path (%s) twice.', folder)
            exit_box()

        #Create folder if doesn't exist
        if not os.path.exists(folder):
            print('Creating folder: ' + folder)
            logger.info('Creating folder %s', folder)
            try:
                os.makedirs(folder)
            except:
                print('Error creating folder: %s' % folder)
                logger.error('Error creating folder %s', folder)
                
                
    # check label path
    if hasattr(config, "label_path") and not os.path.exists(config.label_path):
        config.label_path = None

def intro():
    # intro screen
    intro_image = camera.get_path() + "/assets/intro.png"
    return camera.overlay_image(intro_image, 0, 4)
        
def main():
    overlay_intro = intro()

    i = 0
    error_overlay = None
    error_message = False
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
            
            # remove intro overlay 
            if overlay_intro is not None:
                camera.remove_overlay(overlay_intro)
                overlay_intro = None
                
            # Print is started despite dome is pressed => there was an error => cancel print job
            if boxio.print_started():
                print("Dome is pressed despite printin in progress => Error?")
                logger.warning("Dome is pressed despite printin in progress => Error?")
                boxio.set_print_led(False)
                boxio.reset_print_pressed()
                boxio.cancel_print_job()
                if not error_overlay is None:
                    camera.remove_overlay(error_overlay)
                    error_overlay = None
                error_message = False
            
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
            
            # save photos into backup folder
            if hasattr(config, "images_folder_copy") and isinstance(config.images_folder_copy, list):
                for dest in config.images_folder_copy:
                    for src in photo_filenames:
                        print(src + ' -> ' + dest)
                        logger.info('Copy %s -> %s', src, dest)
                        try:
                            shutil.copy2(src, dest)
                            print("Copied")
                        except shutil.Error as e:
                            print("Error: %s" % e)
                            logger.error('Error: %s ', e)
                        except IOError as e:
                            print("Error: %s" % e.strerror)
                            logger.error('Error: %s ', e.strerror)            
            
            # enable buttons
            boxio.reset_dome_pressed()
            boxio.enable_buttons()
            
            # show montage in layer 5
            camera.show_image()
            
            # show intro in layer 4
            overlay_intro = intro()
        
        # Print Button Pressed
        if boxio.is_print_pressed():
           
            # Start print
            if not boxio.print_started():
                print("Print pressed")
                logger.info('Print pressed')
                # Disable Front User Buttons only so no new photo/print can be triggered
                boxio.disable_buttons(True)
                
                filename = camera.get_image()
                print_id = boxio.print_image(filename)
                error_overlay = camera.overlay_text_as_image(config.lang["printer_started"], 5, 0, 30, 50)
            
            # Retry print job 
            if error_message:
                print("PRINTER Pressed (again)")
                logger.debug("PRINTER PRESSED (again)")
                boxio.cancel_print_job(True)
                
                if not error_overlay is None:
                    camera.remove_overlay(error_overlay)
                    error_overlay = camera.overlay_text_as_image(config.lang["printer_started"], 5, 0, 30, 50)
                
                error_message = False
                
                # when there was an error the front buttons are enabled => disable them again
                boxio.disable_buttons(True)
                
            boxio.reset_print_pressed()
        
        # Currently printing
        if boxio.print_started():
            
            # Print has errors      
            error = boxio.has_print_error()
            if not error == False and error_message == False:
                print("PRINT ERROR")
                logger.debug("PRINT ERROR")
                logger.debug(error)
                if not error_overlay is None:
                    camera.remove_overlay(error_overlay)
                    
                if "ribbon" in error.lower():
                    message = config.lang["error_ribbon"]
                elif "paper" in error.lower():
                    message = config.lang["error_paper"]
                else:
                    message = config.lang["error_printer"]
                error_overlay = camera.overlay_text_as_image(message, 5, 0, 30, 50)
                error_message = True
                
                # Enable front buttons so that we can make a new photo
                boxio.enable_buttons(True)
            
            # Print finished
            if boxio.printed():
                print("PRINT FINISHED")
                logger.debug("PRINT FINISHED")
                boxio.set_print_led(False)

                if not error_overlay is None:
                    camera.remove_overlay(error_overlay)
                    error_overlay = None
                
                error_message = False
                boxio.enable_buttons(True)
                
            else:
                # Blink the Print LED
                if i%config.blink_speed == 4:
                    boxio.set_print_led(True)
                elif i%config.blink_speed == 0:
                    boxio.set_print_led(False)
        else:
            # Hide last image? only if not printing
            camera.hide_image_if_needed()
            

        # Exit Button pressed
        if boxio.is_exit_pressed():
            print("Exit pressed")
            logger.info('Exit pressed')
            raise Exception('Exit Button pressed')

        sleep(0.1)


        
# check folder existence
check_folders()

boxio = BoxIO(config)
leds = LEDs(0,0,config.pixel_count)
camera = Camera(config)
        
        
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
         