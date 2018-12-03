#GPIO PINs
btn_single = 17     # pin that the 'take 1 photo' button is attached to
btn_multi  = 22     # pin that the 'take multiple photos' button is attached to
btn_print  = 27     # pin that the 'print photo' button is attached to
btn_dome   = 18     # pin that the big dome button is attachted to
btn_exit   = 4      # pin that the 'exit' button is attached to
btn_relay  = 23     # pin that triggers the relay
led_single = 12     # pin that the single led is attached to
led_multi  = 6      # pin that the multi led is attached to
led_print  = 16     # pin that the print led is attached to
led_dome   = 5      # pin that the big dome led is attached to
relay      = 24     # pin that the relay for enable the printer is connected

# WS2801 LED count
pixel_count = 14    

# max resolution:
# v1: 2592x1944
# v2: 3280x2464 

# the photo resolution must be 3:2 ( image + label) because the printer has an image format of 150mm:100mm
# a width of 1920px therefore needs a height of 1280px
# the label is subtracted from the height so for a 128px label the photo height is 1152px
photo_w    = 1920   # photo resolution
photo_h    = 1280
photo_hflip = True
preview_hflip = False

# the path to the label
# if there should be no label you need to can comment this entry out
label_path  = "/media/pi/INTENSO/label.jpg"
label_h     = 128

# display resolution
screen_w   = 1024   
screen_h   = 600

# number of images for multi shot
image_count = 4     

# blink speed of dome led
blink_speed = 8     

# number of seconds as users prepare to have photo taken
prep_delay  = 2             

# countdown time before photo is taken
photo_countdown_time = 10    

# show the final image for x seconds (0 for endless)
show_image_time = 60

# Primary folder to save images to (required):
images_folder = "photos"

# Additional locations where images will be saved to (optional):
images_folder_copy = ["/home/pi/photos", "/media/pi/INTENSO/photos"]

