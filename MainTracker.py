import libjevois as jevois
import cv2
import numpy as np
import json
#Holders for target data
pixels = [(0,0), (0,0), (0,0), (0,0)]


# Values to use in target distance calculation
Ta = 6 #Actual target width in inches
Fd = 65.0  #Camera View in degrees. JeVois = 65.0, Lifecam HD-300 = 68.5, Cinema = 73.5

##Threshold values for Trackbars, These are pulled from the CalFile
CalFile = open ('Calibration').read().split(",")
uh = int(CalFile[0])
lh = int(CalFile[1])
us = int(CalFile[2])
ls = int(CalFile[3])
uv = int(CalFile[4])
lv = int(CalFile[5])
er = int(CalFile[6])
dl = int(CalFile[7])
ap = int(CalFile[8])
ar = 0
sl = float(CalFile[10])


class Tracker:
    # ###################################################################################################
    ## Constructor
    def __init__(self):
        # Instantiate a JeVois Timer to measure our processing framerate:
        self.timer = jevois.Timer("Catbox", 100, jevois.LOG_INFO)
    
    
    def process(self, inframe):
                # Get the next camera image (may block until it is captured) and here convert it to OpenCV BGR by default. If
        # you need a grayscale image instead, just use getCvGRAY() instead of getCvBGR(). Also supported are getCvRGB()
        # and getCvRGBA():
        inimg = inframe.getCvBGR()

        # Start measuring image processing time (NOTE: does not account for input conversion time):
        self.timer.start()
        #Convert the image from BGR(RGB) to HSV
        hsvImage = cv2.cvtColor(inimg, cv2.COLOR_BGR2HSV)
        
        ## Threshold HSV Image to find specific color
        binImage = cv2.inRange(hsvImage, (lh, ls, lv), (uh, us, uv))
        
        # Erode image to remove noise if necessary.
        binImage = cv2.erode(binImage, None, iterations = er)
        #Dilate image to fill in gaps
        binImage = cv2.dilate(binImage, None, iterations = dl)
        
                
        ##Finds contours (like finding edges/sides), 'contours' is what we are after
        im2, contours, hierarchy = cv2.findContours(binImage, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_KCOS)
        
        ##arrays to will hold the good/bad polygons
        squares = []
        badPolys = []
        finalShapes = []
        areas = {}
        thresh = 5000

        
        ## Parse through contours to find targets
        for c in contours:
            if (contours != None) and (len(contours) > 0):
                cnt_area = cv2.contourArea(c)
                hull = cv2.convexHull(c , 1)
                hull_area = cv2.contourArea(hull)  #Used in Solidity calculation
                p = cv2.approxPolyDP(hull, ap, 1)
                if (cv2.isContourConvex(p) != False) and (len(p) == 4) and (cv2.contourArea(p) >= ar) and (cv2.contourArea(p) <= ar+76800):
                    filled = cnt_area/hull_area
                    if filled <= sl:
                        squares.append(p)
                else:
                    badPolys.append(p)
        
        
        
        if len(squares) > 1:
            counter = 0
            for s in squares:
                cnt_area = cv2.contourArea(s)
                hull = cv2.convexHull(s , 1)
                hull_area = cv2.contourArea(hull)  #Used in Solidity calculation
                p = cv2.approxPolyDP(hull, ap, 1)
                areas[counter] = cv2.contourArea(p)
                counter = counter+1
            
            largestIndex = max(areas.keys())
            largest = max(areas.values())
            del areas[largestIndex]
            secondLargest = -100
            for i in range(len(areas.keys())):
                if abs(largest - max(areas.values())) <= thresh:
                    secondLargest = max(areas.keys())
                    
            if secondLargest != -100:
                finalShapes.append(squares[int(largestIndex)])
                finalShapes.append(squares[int(secondLargest)])




        for s in finalShapes:
            MyVariables.counter = 0
            br = cv2.boundingRect(s)
            #Target "x" and "y" center 
            x = br[0] + (br[2]/2)
            y = br[1] + (br[3]/2)
            if MyVariables.otherx > -100:
            
                if x > MyVariables.otherx:
                    calcX = x - MyVariables.otherx
                elif MyVariables.otherx > x:
                    calcX = MyVariables.otherx - x
                else:
                    calcX = 0
                
                if calcX != 0:
                    MyVariables.Distance = 1920/calcX
                

                MyVariables.pixels = [1,x,,y]
                MyVariables.pixels2 = [0,x,y]



            MyVariables.otherx = x
            
            
        if not finalShapes:
            MyVariables.pixels = 0
            
        if MyVariables.pixels == 0 and MyVariables.counter < 25:
            json_pixels = json.dumps(MyVariables.pixels2)
            MyVariables.counter = MyVariables.counter+1
        else:
            json_pixels = json.dumps(MyVariables.pixels)
        

        # Convert our BGR output image to video output format and send to host over USB. If your output image is not
        # BGR, you can use sendCvGRAY(), sendCvRGB(), or sendCvRGBA() as appropriate:
        jevois.sendSerial(json_pixels)
        
class MyVariables:
    otherx = -100
    Distance = -100
    pixels = 0
    pixels2 = 0
    counter = 0
            
        
        
