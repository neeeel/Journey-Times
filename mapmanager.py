import io
import urllib.request
from PIL import Image
import math
from math import log, exp, tan, atan, pi, ceil,cos,sin,atan2,sqrt
import bisect


EARTH_RADIUS = 6378137
EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS
INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0

class MapManager():

    def __init__(self, map_height,map_width, zoom, coords,tps):
        self.zoomValues = [0.703, 0.352, 0.176, 0.088, 0.044, 0.022, 0.011, 0.005, 0.003, 0.001, 0.0005]
        self.zoomValues = list(reversed(self.zoomValues))
        self.map_height = map_height
        self.map_width = map_width
        self.zoom = self.calculateZoomValue(tps)
        self.tps = tps
        self.center_lat,self.center_lon = self.get_centre_of_points(tps)
        #print(self.center_lat,self.center_lon)
        #self.center_lon = coords[1]

        self.static_map = self.load_map(self.center_lat, self.center_lon)
        self.static_map_sec = self.load_map(self.center_lat, self.center_lon,direction="s")
        self.plotted_points = []

    def get_centre_of_points(self,points):
        points = list(map(self.latlontopixels, points))
        #print("pionts is", points)
        maxX = max(points, key=lambda item: item[0])[0]
        maxY = max(points, key=lambda item: item[1])[1]
        minX = min(points, key=lambda item: item[0])[0]
        minY = min(points, key=lambda item: item[1])[1]
        #print(maxX, minX, maxY, minY)
        centreX = maxX - ((maxX - minX) * 0.5)
        centreY = maxY - ((maxY - minY) * 0.5)
        #print("before conversion", centreX, centreY)
        centre = self.pixelstolatlon((centreX, centreY))
        #print("centre is ",centre)
        return centre

    def calculateZoomValue(self,points):
        #print("points in calc zoom are",points,self.center_lat,self.center_lon)
        maxX = max(points, key=lambda item: item[0])[0]
        maxY = max(points, key=lambda item: item[1])[1]
        minX = min(points, key=lambda item: item[0])[0]
        minY = min(points, key=lambda item: item[1])[1]
        #print(maxX, minX, maxY, minY)
        #print(maxX - minX, maxY - minY)
        maxVal =max(maxX - minX, maxY - minY)
        #print("maxval is ",maxVal)
        #print("calculated zoom as ",20 -bisect.bisect_right(self.zoomValues,maxVal),bisect.bisect_right(self.zoomValues,maxVal))
        for i,z in enumerate(self.zoomValues):
            diff = maxVal-z
            #print("diff ", diff, z,20-i,diff/z,z/diff)
            if diff < 0:
                if abs(diff/z) < 0.15:
                    #print("adding 1 to zoom")
                    zoom = i+1
                else:
                    zoom = i
                break
        #print("second version, zoom is",20 - zoom)
        return 20 - zoom

    def get_map(self):
        return self.static_map

    def get_sec_map(self):
        return self.static_map_sec

    def latlontopixels(self,coords):
        lat, lon = coords
        mx = (lon * ORIGIN_SHIFT) / 180.0
        my = log(tan((90 + lat) * pi/360.0))/(pi/180.0)
        my = (my * ORIGIN_SHIFT) /180.0
        res = INITIAL_RESOLUTION / (2**self.zoom)
        px = (mx + ORIGIN_SHIFT) / res
        py = (my + ORIGIN_SHIFT) / res
        return px, py

    def pixelstolatlon(self,coords):
        px, py = coords
        res = INITIAL_RESOLUTION / (2 ** self.zoom)
        mx = px * res - ORIGIN_SHIFT
        my = py * res - ORIGIN_SHIFT
        lat = (my / ORIGIN_SHIFT) * 180.0
        lat = 180 / pi * (2 * atan(exp(lat * pi / 180.0)) - pi / 2.0)
        lon = (mx / ORIGIN_SHIFT) * 180.0
        return lat, lon

    def get_coords(self,coords,size=800):
        ## takes a lat and long pair, converts them to x,y coordinates that refer to where on the drawing canvas the point is, given that we know the lat,lon of the centre point of the map
        #print("in getcoords, size is",size)
        point = self.latlontopixels(coords)
        centre = self.latlontopixels((self.center_lat,self.center_lon))
        x = centre[0]-point[0]
        y = centre[1]-point[1]
        scaleFactor = size/640
        x*=scaleFactor # scaling factor, because we have stretched the map to 800 by 800
        y*=scaleFactor
        return (size/2) - x, (size/2) + y

    def get_map_with_path(self,tps,path):
        base = 65
        step = int(len(path) / 150) + 1
        noOfPoints = len(path) * 12
        #print("tps are ",tps)
        markers = ""
        pathString = "&path="
        markers += "&markers=color:green%7Clabel:A%7C" + str(self.tps[0][0]) + "," + str(self.tps[0][1])
        for i, tp in enumerate(self.tps[1:-1]):
            markers += "&markers=color:blue%7Clabel:" + chr(i + 1 + base) + "%7C" + str(tp[0]) + "," + str(tp[1])
        markers += "&markers=color:Red%7Clabel:" + chr(len(self.tps) - 1 + base) + "%7C" + str(self.tps[-1][0]) + "," + str(self.tps[-1][1])
        for p in path[::step]:
            pathString+= str(p[0]) + "," + str(p[1]) + "%7C"
        pathString += str(path[-1][0]) + "," + str(path[-1][1])
        url = "http://maps.googleapis.com/maps/api/staticmap?&size=" + str(self.map_width) + "x" + str(self.map_height) + markers + pathString + "&key=AIzaSyAQl_6HX3wWlZRpG96XDhdDWZ07_3R6Df4"
        print("url for route map is",url)
        buffer = urllib.request.urlopen(url)
        image = Image.open(buffer).convert('RGB')
        return image

    def change_zoom(self,val):
        self.zoom+=val
        return self.load_map(self.center_lat, self.center_lon)

    def load_map(self,lat,lon,direction="p"):
        markers = ""
        base = 65
        if direction=="p":
            timingPoints = self.tps
        else:
            print("secondary map")
            timingPoints = list(reversed(self.tps))

        markers += "&markers=color:green%7Clabel:A%7C" + str(timingPoints[0][0]) + "," + str(timingPoints[0][1])
        for i, tp in enumerate(timingPoints[1:-1]):
            markers += "&markers=color:blue%7Clabel:" + chr(i + 1 + base) + "%7C" + str(tp[0]) + "," + str(tp[1])
        markers += "&markers=color:Red%7Clabel:" + chr(len(timingPoints) -1 + base) + "%7C" + str(timingPoints[-1][0]) + "," + str(timingPoints[-1][1])
        #print("markers is", markers)
        url = "http://maps.googleapis.com/maps/api/staticmap?center=" + str(lat) + "," + str(lon) + "&size=" + str(self.map_width) + "x" + str(self.map_height) + "&zoom=" + str(self.zoom) + "&sensor=false&scale=2" + markers + "&key=AIzaSyAQl_6HX3wWlZRpG96XDhdDWZ07_3R6Df4"
        print(url)
        buffer = urllib.request.urlopen(url)
        image = Image.open(buffer).convert('RGB')
        val = 800
        image = image.resize ((val,val),Image.ANTIALIAS)
        self.map_height=val
        self.map_width = val
        if direction=="p":
            image.save('map.jpg')
        else:
            image.save("sec_map.jpg")
        return image

    def get_thumbnail(self):
        if self.static_map is None:
            return
        image = Image.open("map.jpg")
        val = 800
        image = image.resize((val, val), Image.ANTIALIAS)
        return image

    def _window_x_y_to_grid(self, x, y):
        '''
        converts graphical x, y coordinates to grid coordinates
        where (0, 0) is the very center of the window
        takes in the actual windows co-ords, and returns relative coords
        '''
        center_x = self.map_width / 2
        center_y = self.map_height / 2
        new_x = x - center_x
        new_y = -1 * (y - center_y)
        return new_x, new_y

    def update_values(self,height,width):
        self.map_height = height
        self.map_width = width

    def grid_x_y_to_window(self,grid_x,grid_y):
        center_x = self.map_width / 2
        center_y = self.map_height / 2
        new_x = grid_x + center_x
        new_y = 1 * (grid_y + center_y)
        return new_x, new_y

    def x_y_to_lat_lon(self, x, y):
        grid_x, grid_y = self._window_x_y_to_grid(x, y)
        offset_x_degrees = (float(grid_x) / self.map_width) * self.degrees_in_map
        offset_y_degrees = (float(grid_y) / self.map_height) * self.degrees_in_map
        # lat = y, lon = x
        return self.center_lat + offset_y_degrees, self.center_lon + offset_x_degrees

    def lat_lon_to_x_y(self,lat,lon):
        offset_y_degrees = lat - self.center_lat
        offset_x_degrees = lon - self.center_lon
        grid_y = -1 * (offset_y_degrees / self.degrees_in_map) * self.map_height
        grid_x = (offset_x_degrees / self.degrees_in_map) * self.map_width
        #return grid_x,grid_y
        return self.grid_x_y_to_window(grid_x,grid_y)

    @property
    def degrees_in_map(self):
        '''
        This logic is based on the idea that zoom=0 returns 360 degrees
        '''
        return (self.map_height / 256.0) * (360.0 / pow(2, self.zoom))





points = [(56.40501,-3.45778),(56.40716,-3.48441),(56.44521,-3.47190)] # route 3
points = [(56.38288,-3.40631),(56.44521,-3.47190),(56.36840,-3.42832)] # route 1
#points = [(54.3338,-7.66276) ,(54.3338,-7.66279), (54.333309999999997, -7.6634900000000004)]
#mp = MapManager(640,640,11,(56.40501,-3.45778),points)
#print(mp.get_centre_of_points(points))

#exit()


