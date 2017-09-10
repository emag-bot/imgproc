
import cv2
import numpy as np
import urllib
#from matplotlib import pyplot as plt

class PathLocation:
    OFFLINE = 0
    ONLINE  = 1

class ImageAnalyser:
    img = None

    def __init__(self):
        pass
    
    def LoadImage(self, path, path_location = PathLocation.OFFLINE):
        if path_location == PathLocation.ONLINE:
            resp = urllib.urlopen(path)
            self.img = np.asarray(bytearray(resp.read()), dtype="uint8")
            self.img = cv2.imdecode(self.img, cv2.IMREAD_COLOR)
        else:
            self.img = cv2.imread(path, cv2.IMREAD_UNCHANGED)

        self.img = cv2.resize(self.img, (512, 512))

    def AutoCanny(self, image, sigma=0.33):
        # compute the median of the single channel pixel intensities
        v = np.median(image)

        # apply automatic Canny edge detection using the computed median
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))
        edged = cv2.Canny(image, lower, upper)

        # return the edged image
        return edged

    def FindContour(self):
        if self.img is None:
            print("No image was loaded.")
            exit()

        img_b = cv2.GaussianBlur(self.img, (7, 7), 0)
        img_segm = cv2.pyrMeanShiftFiltering(img_b, 40, 45, 3)
        
        edges = self.AutoCanny(img_segm)
        edges = cv2.adaptiveThreshold(edges, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 3, 1)

        kernel = np.ones((3,3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        edges = cv2.erode(edges, kernel, iterations=1)

        im2, contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        contour_sizes = [(cv2.contourArea(contour), contour) for contour in contours]
        biggest_contour = max(contour_sizes, key=lambda x: x[0])[1]
        biggest_contour = cv2.convexHull(biggest_contour)
        self.DrawContours(self.img, [biggest_contour])
        self.ShowImage(self.img, "contours")

        return biggest_contour
    
    def ExtractContour(self, contour):
        stencil = np.zeros(self.img.shape).astype(self.img.dtype)
        cv2.fillPoly(stencil, [contour], [255,255,255])
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(30,30))
        closing = cv2.morphologyEx(stencil, cv2.MORPH_CLOSE, k)
        img_extracted = cv2.bitwise_and(self.img, stencil)

        return closing

    def DrawContours(self, img, contours):
        cv2.drawContours(img, contours, -1, (0,255,0), 1)

    def GetHueHistogram(self, img):
        img_hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(img_hsv)

        ret, mask = cv2.threshold(v, 0, 255, cv2.THRESH_BINARY)

        hist_item = cv2.calcHist([h], [0], mask, [180], [0,180])
        cv2.normalize(hist_item,hist_item,0,1,cv2.NORM_MINMAX)

        return hist_item

    def ShowImage(self, img, name):
        cv2.imshow(name, img)
        cv2.waitKey(0)
