import time
import random
from threading import Thread


from sensor import Sensor

import numpy as np
import cv2

from find_gauge_circle import find_gauge_circle
from find_needle import find_needle4



class RealSensor(Sensor):
    def __init__(self,manager):
        super().__init__(manager)
        self.find_center_count = 5  # every [find_center_count] frames the gauge self.camera_idx/size is found
        self.crop = True  # crop the input images to squares?
        self.flip = True  # flip input images in both dimensions to reorient?
        self.camera_idx = 0  # who is taking the pictures?
        self.running = False
        self.latest_raw_image = []
        self.scaledown = 1
        self.hist_frac = 1
        self.k_size = 1
        self.latest_display_info = None
        self.cap = None

    # take single image to initialize final parameters
    def initialize_parameters(self):
        
        # wake up camera by giving it something to do and pausing
        # not sure if this is needed outside of my computer...
        self.cap = cv2.VideoCapture(self.camera_idx)
        ret, img = self.cap.read()
        time.sleep(2)

        img2,crop_scale = self.get_bw_image()   
        if len(img2) > 0:
            self.hist_frac = 0.1 / crop_scale # image size affects percentile of darkness to threshold

            self.scaledown = np.round(np.shape(img2)[0]/360) # image size affects scaledown factor
            self.k_size=int(np.round(10/self.scaledown)) # scaledown factor affects morphological kernel for circle finding



    # initialize parameters and take/send continuous theta measurements
    def run(self,live_feed=True,find_circle_continuously=False):
        self.live_feed = live_feed
        self.initialize_parameters()

        # no center point yet, initialize counter
        center_pt = None
        counter = 0
        rad = None

        self.running = True
        Thread(target=self.image_getter_loop, args=[{}]).start()
        Thread(target=self.update_display, args=[{}]).start()

        while self.running:
            img2 = self.latest_raw_image

            if len(img2) > 0:
                # down-scale image by factor [scaledown], also downscale binary erosion kernel (for circle finding)
                img2 = cv2.resize(img2, tuple(int((i/self.scaledown)) for i in img2.shape[::-1]), interpolation = cv2.INTER_AREA)

                # trigger center-finding every [find_center_count] frames
                if counter ==0:

                    old_center = center_pt
                    old_rad = rad

                    center_pt, rad = find_gauge_circle(img2,prev_loc=center_pt,hist_frac=self.hist_frac,k_size=self.k_size)
                    counter = -self.find_center_count

                    # prevent problematic shifts and scalings as a fail safe. [maybe not necessary?]
                    if not old_center is None and (abs(rad-old_rad)/min([rad,old_rad]) > 0.2 or any(((i-j)**2 for i,j in zip(old_center,center_pt)))>old_rad*0.2):
                        rad,center_pt = old_rad,old_center

                    # radius range to avoid tick marks (higher value) and 
                    # capture thick back of needle (lower value)
                    R = [int(0.4*rad),int(0.55*rad)] 

                    # recalculate the histogram fraction for circle finding next time.
                    # area of annulus between rad and 1.2*rad circles
                    self.hist_frac = 3.14*(0.44*rad**2)/np.size(img2)

                if find_circle_continuously:
                    counter += 1

                
                # find theta value of needle. Theta sorting memoized, saves ~10% time
                theta = find_needle4(img2,center_pt,R)



                self.manager.updateReadings(self.convert_theta_to_inH2O(theta))

                self.latest_display_info = {
                    'rad': rad,
                    'theta': theta,
                    'center_pt': center_pt,
                    'img2': img2
                }


            # Yield the thread
            time.sleep(0)


        # When everything done, release the capture
        if self.live_feed:
            self.cap.release()
            cv2.destroyAllWindows()


    def update_display(self, params):
        while self.running:
            if self.live_feed and self.latest_display_info:
                # plot found circle and needle location on top of image                
                rad = self.latest_display_info.get('rad')
                theta = self.latest_display_info.get('theta')
                center_pt = self.latest_display_info.get('center_pt')
                img2 = self.latest_display_info.get('img2')

                center_pt = tuple(np.array(center_pt,dtype=int))
                needle_pt = tuple(center_pt + np.array([-rad*np.sin(theta),rad*np.cos(theta)],dtype=int))

                img2 = cv2.line(img2, center_pt, needle_pt, (255,255,255) , 2) 
                img2 = cv2.circle(img2, center_pt, int(rad), (255,255,255), 1) 

                # Display the resulting frame
                winname = "Pressure Gauge (inH2O)"
                cv2.namedWindow(winname)        # Create a named window
                cv2.moveWindow(winname, 541,0)  # Move it to (0,0)
                cv2.resizeWindow(winname, 480, 563)
                cv2.imshow(winname, img2)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False


    def image_getter_loop(self, params):
        while self.running:
            latest_raw_image, _ = self.get_bw_image()
            self.latest_raw_image = latest_raw_image
            time.sleep(0)
    
    # function that returns image from file or camera, 
    # and optionally flips and/or crops image to square
    def get_bw_image(self):
        
        # capture image
        ret, img = self.cap.read()

        S = np.shape(img)

        if not S:
            return ([], None)

        # remove wings of image so it is square (if width>height)
        if self.crop and S[0]<S[1]: 
            S_half = int(S[0]/2) # half of height
            cp = int(S[1]/2) # half of width
            img = img[:,(cp-S_half):(cp+S_half),:]
            img_frac = S[0]/S[1]
        else:
            img_frac = 1
        
        if self.flip:
            img = cv2.rotate(img, cv2.ROTATE_180)
            
        #Make black and white, and return (image, image_fractional_size)
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),img_frac


    def convert_theta_to_inH2O(self,theta):
        # 0.89 is location of 0 in H20
        # 5.46 is location of 35 in H20
        
        #return ((theta-0.89)/(5.46-0.89))*35
        #return (((theta*57.2958)-42)/(270))*35
        if ((((theta*57.2958)-42)/(270))*35) < 1:
            return 0
        else:
            return (((theta*57.2958)-42)/(270))*35
