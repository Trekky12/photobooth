#!/usr/bin/env python3

import picamera
from PIL import Image, ImageFont, ImageDraw
import numpy as np
from time import sleep

import datetime
import subprocess
import os

import logging

logger = logging.getLogger("photobooth")

class Camera:
    photo_w         = 1920
    photo_h         = 1280
    screen_w        = 1024
    screen_h        = 600
    image_count     = 4
    prep_delay      = 2
    images_folder   = 'photos'
    label_path      = None
    label_h         = 0
    photo_countdown_time = 3
    image_overlay       = -1    # Preview of montage
    base_filename       = None
    final_image         = None
    image_mode_multi    = False
    photo_hflip         = True
    preview_hflip       = True
    show_image_time     = 0


    def __init__(self, config):
        if hasattr(config, "photo_w"):
            self.photo_w = config.photo_w
        if hasattr(config, "photo_h"):
            self.photo_h = config.photo_h
        if hasattr(config, "screen_w"):
            self.screen_w = config.screen_w
        if hasattr(config, "screen_h"):
            self.screen_h = config.screen_h
        if hasattr(config, "image_count"):
            self.image_count = config.image_count
        if hasattr(config, "images_folder"):
            self.images_folder = config.images_folder
        if hasattr(config, "prep_delay"):
            self.prep_delay = config.prep_delay    
        if hasattr(config, "photo_countdown_time"):
            self.photo_countdown_time = config.photo_countdown_time                
        if hasattr(config, "label_path"):
            self.label_path = config.label_path       
        if hasattr(config, "label_h"):
            self.label_h = config.label_h  
        if hasattr(config, "photo_hflip"):
            self.photo_hflip = config.photo_hflip  
        if hasattr(config, "preview_hflip"):
            self.preview_hflip = config.preview_hflip
        if hasattr(config, "show_image_time"):
            self.show_image_time = config.show_image_time            
            
        # create absolute path
        self.path = os.path.dirname(os.path.realpath(__file__))
    
        #Setup Camera
        try:
            self.camera = picamera.PiCamera()
        except:
            print("error initializing the camera - exiting")
            logger.error("error initializing the camera - exiting")
            raise SystemExit
            
        self.camera.annotate_text_size = 80
        
        # subtract label height
        if not self.label_path is None:
            self.photo_h = self.photo_h - self.label_h
        
        self.camera.resolution = (self.photo_w, self.photo_h)
        
        # the image preview is flipped horizontally
        self.camera.hflip = self.photo_hflip 
        
        # start camera preview
        self.camera.start_preview(resolution=(self.screen_w, self.screen_h), hflip=self.preview_hflip)
        
        # show preview only right before capturing
        # the preview is in layer 2
        self.camera.preview.alpha = 0
        
        # Create static black background overlay in layer 1
        self.overlay_background()
        
    def get_path(self):
        return self.path
        
    def set_image_mode_multi(self, image_mode_multi):
        self.image_mode_multi = image_mode_multi
        
    def overlay_text(self,text):
        self.camera.annotate_text = text
        
    def overlay_countdown(self):
        countdownFont = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", 80)
        countdownImage = Image.new("RGBA", (self.screen_w,self.screen_h), (0,0,0,0))
        countdown_overlay = self.camera.add_overlay(countdownImage.tobytes(), size=(self.screen_w, self.screen_h), format='rgba', layer=5)

        for counter in range(self.photo_countdown_time,0,-1):
            img = countdownImage.copy()
            draw = ImageDraw.Draw(img)
            draw.text((self.screen_w/2,50), "..." + str(counter), (255,255,255), font=countdownFont)
            
            # create new overlay with countdown number
            countdown_overlay_new = self.camera.add_overlay(img.tobytes(), size=(self.screen_w, self.screen_h), format='rgba', layer=5)
            # remove previous overlay
            self.camera.remove_overlay(countdown_overlay)
            # save this overlay as previous 
            countdown_overlay = countdown_overlay_new
            sleep(1)
        # remove last overlay
        self.camera.remove_overlay(countdown_overlay)
        
    def remove_overlay(self,overlay_id):
        if overlay_id != -1:
            self.camera.remove_overlay(overlay_id)
        
    def overlay_image(self, image_path, duration=0, layer=4):
        """
        Add an overlay (and sleep for an optional duration).
        If sleep duration is not supplied, then overlay will need to be removed later.
        This function returns an overlay id, which can be used to remove_overlay(id).
        """

        # "The camera`s block size is 32x16 so any image data
        #  provided to a renderer must have a width which is a
        #  multiple of 32, and a height which is a multiple of
        #  16."
        #  Refer: http://picamera.readthedocs.io/en/release-1.10/recipes1.html#overlaying-images-on-the-preview

        # Load the arbitrarily sized image
        img = Image.open(image_path)

        # Create an image padded to the required size with
        # mode 'RGB'
        pad = Image.new('RGB', (
            ((img.size[0] + 31) // 32) * 32,
            ((img.size[1] + 15) // 16) * 16,
        ))

        # Paste the original image into the padded one
        pad.paste(img, (0, 0))

        #Get the padded image data
        try:
            padded_img_data = pad.tobytes()
        except AttributeError:
            padded_img_data = pad.tostring() # Note: tostring() is deprecated in PIL v3.x

        # Add the overlay with the padded image as the source,
        # but the original image's dimensions
        o_id = self.camera.add_overlay(padded_img_data, size=img.size)
        o_id.layer = layer
        

        if duration > 0:
            sleep(duration)
            self.camera.remove_overlay(o_id)
            return -1 # '-1' indicates there is no overlay
        else:
            return o_id # we have an overlay, and will need to remove it later    
            
            
    def overlay_background(self, layer = 1, alpha = 255):
        a = np.zeros((self.screen_h, self.screen_w, 3), dtype=np.uint8)
        o_bg = self.camera.add_overlay(a, size=(self.screen_w, self.screen_h), format='rgb', layer=layer)
        o_bg.alpha = alpha
        
        
    def prep_for_photo_screen(self, photo_number):
        if photo_number > 1:
            get_ready_image = self.path + "/assets/get_ready_next.png"
        else:
            get_ready_image = self.path + "/assets/get_ready.png"
        self.overlay_image(get_ready_image, self.prep_delay)

    def show_image(self):        
        filename = self.get_image()
        self.image_overlay = self.overlay_image(filename, 0, 5)
        if self.show_image_time > 0:
            sleep(self.show_image_time)
            self.hide_image()
        
    def hide_image(self):
        if self.image_overlay != -1:
            self.remove_overlay(self.image_overlay)
            self.image_overlay = -1
            # Reset current image
            self.base_filename = None
            self.final_image = None
            
    def get_image(self):
        if self.final_image is not None:
            return self.final_image
        return None
    
    def create_file_name(self):
        base_filename = self.path + '/' + self.images_folder + '/' + str(datetime.datetime.now()).split('.')[0]
        base_filename = base_filename.replace(' ', '_')
        base_filename = base_filename.replace(':', '-')
        self.base_filename = base_filename
    
    def capture(self, photo_number):

        if self.base_filename is None:
            self.create_file_name()
    
        # set resolution and filename
        if self.image_mode_multi:
            filename = self.base_filename + '_multi_' + str(photo_number) + 'of'+ str(self.image_count)+'.jpg'
            
            # for the multi image the picture can be half width/height and the tile spacing (2*10) must be subtracted
            photo_w_multi = round(self.photo_w / 2.0) - (2*10)
            photo_h_multi = round(self.photo_h / 2.0) - (2*10)
            
            self.camera.resolution = (photo_w_multi, photo_h_multi)
            
        else:
            filename = self.base_filename + '_single.jpg'
            
            # resolution for single shot is full shot
            photo_w_single = self.photo_w
            photo_h_single = self.photo_h
            
            self.camera.resolution = (photo_w_single, photo_h_single)
            
        # it is possible that the preview resolution is smaller when switching from
        # mode multi to mode single so reset the resolution here
        # see https://github.com/waveform80/picamera/blob/master/picamera/renderers.py#L516-L520
        if self.camera.resolution.width > self.screen_w and self.camera.resolution.height > self.screen_h:
            self.camera.preview.resolution = (self.screen_w, self.screen_h)

        # show preview
        self.camera.preview.alpha = 255    
            
        # countdown from photo_countdown_time, and display countdown on screen
        #for counter in range(self.photo_countdown_time,0,-1):
        #    self.overlay_text("             ..." + str(counter))
        #    sleep(1)
        self.overlay_countdown()

        # capture
        self.camera.annotate_text = ''
        self.camera.capture(filename)
        
        # hide preview
        self.camera.preview.alpha = 0
        print("Photo saved: " + filename)
        logger.info("Photo saved: %s", filename)        
        
        return filename


    def convertMergeImages(self):
        """
        This function merges the images when multi mode is selected
        inspired by https://github.com/zoroloco/boothy/blob/master/pbooth.py
        and https://github.com/safay/RPi_photobooth/blob/master/assemble_and_print
        """

        # Processing
        print("Processing...")
        logger.info("Processing...")      
        processing_image = self.path + "/assets/processing.png"
        processing_overlay = self.overlay_image(processing_image)
        
        filename = self.base_filename + '_montage.jpg'

        # combine the 4 images
        if self.image_mode_multi:
            IMG1 = "%s_multi_%sof%s.jpg" % (self.base_filename, 1, self.image_count)
            IMG2 = "%s_multi_%sof%s.jpg" % (self.base_filename, 2, self.image_count)
            IMG3 = "%s_multi_%sof%s.jpg" % (self.base_filename, 3, self.image_count)
            IMG4 = "%s_multi_%sof%s.jpg" % (self.base_filename, 4, self.image_count)
            
            fileNameTemp = self.base_filename + '_montageTemp.jpg'
            
            subprocess.call(["montage", IMG1,IMG2,IMG3,IMG4,"-tile", "2x2", "-geometry", "+10+10",fileNameTemp])
            
        else:
            fileNameTemp = self.base_filename + '_single.jpg'

        
        if self.label_path is not None:
            # prepare filename for correct width
            fileNameTemp = "%s[%sx%s]" % (fileNameTemp, self.photo_w, self.photo_h)
            
            # append label to image
            label = "%s[%sx%s]" % (self.label_path, self.photo_w, self.label_h)
            
            # when using geometry +0+0 the concatenate mode is selected which is okay here
            # see http://www.imagemagick.org/Usage/montage/#zero_geometry
            subprocess.call(["montage",fileNameTemp,label,"-tile", "1x2","-geometry", "+0+0",filename])
        
        else:
            filename = fileNameTemp
            
        
        # set the final name
        self.final_image = filename
                                            
        print("Images have been merged.")
        logger.info("Images have been merged.")      
        self.remove_overlay(processing_overlay)
        
        return filename
        
        
    def stop(self):
        self.camera.stop_preview()
        self.camera.close()
