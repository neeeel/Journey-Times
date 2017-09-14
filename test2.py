import xml.etree.ElementTree as ET
#from fastkml import kml
#import MainWindow
import datetime
import pandas as pd
import openpyxl
import win32com.client
import pandas as pd
import numpy as np
import tkinter
from tkinter import ttk
import mapmanager
from PIL import Image,ImageDraw,ImageTk

import tkinter
import tkinter.ttk as ttk
import tkinter.font as font
import datetime
import mapmanager
import openpyxl
import win32com.client
from PIL import Image,ImageDraw,ImageTk,ImageFont
from tkinter import filedialog
from tkinter import messagebox
import threading
import queue
import copy
import time
import os

class Route():

    ###
    ### this class holds the data for a route
    ### timing points, name, direction, and the thumbnail map

    def __init__(self,name,dir):
        self.name = name
        self.dir = [dir]
        self.timingPoints = []
        self.tracks =[]
        self.mapImage = None
        self.mapManager = None

    def setMapManager(self,mapMan):
        self.mapManager=mapMan

    def update_zoom(self,val):
        self.mapImage = self.mapManager.change_zoom(val)

    def getMapManager(self):
        return self.mapManager

    def add_timing_point(self,lat,long,dir,ID):
        print("adding timing point to route",self.name,"id is",ID,"type of id is ",type(ID))
        self.timingPoints.append((int(ID),dir,float(lat),float(long)))
        self.timingPoints = sorted(self.timingPoints, key=operator.itemgetter(1, 0))
        if not dir in self.dir:
            self.dir.append(dir)

    def add_map(self,image):
        self.mapImage = image
        #self.mapImage.show()

    def get_map(self):
        print("size of map",self.mapImage.size)
        return self.mapImage

    def add_track(self,track):
        self.tracks.append(track)

    def get_timing_points(self):
        TPs = []
        #print(self.dir)
        for d in self.dir:
            l = [tp for tp in self.timingPoints if tp[1] == d]
            l =sorted(l,key=lambda x: x[0])
            TPs.append(l)
        if len(self.dir) == 1:
            reverse = list(reversed(TPs[0]))
            TPs.append(reverse)
        print("returning sorted timing points",TPs)
        return TPs

    def display(self):
        #print(self.name)
        print("---------------------------")
        for tp in self.timingPoints:
            print(tp[0],tp[1]," : ",tp[2],tp[3])


try:
  from lxml import etree
  print("running with lxml.etree")
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
    print("running with cElementTree on Python 2.5+")
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
      print("running with ElementTree on Python 2.5+")
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
        print("running with cElementTree")
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
          print("running with ElementTree")
        except ImportError:
          print("Failed to import ElementTree from any known place")

def kml(file,index):
    result = []
    routes = {}
    dir = "C:\\user\\nwatson\\desktop\\"
    #file = filedialog.askopenfilename(initialdir=dir)
    if file == "":
        return
    if file[-4:] == ".kml":
        tree = etree.parse(file)
        root = tree.getroot()
        #"root",root.tag)
        #for child in root:
            #print(child.tag,child.attrib)
        doc = root.find("{http://www.opengis.net/kml/2.2}Document")
        if doc is None:
            return
        if doc.find("{http://www.opengis.net/kml/2.2}Folder") is None:
            #print("assigning doc")
            iter = root.iter("{http://www.opengis.net/kml/2.2}Document")
        else:
            #print("assigning folder")
            iter = doc.iter("{http://www.opengis.net/kml/2.2}Folder")
        t = []
        for item in iter:
            tps = []

            for track in item.iter("{http://www.google.com/kml/ext/2.2}Track"):
                times = [when.text for when in track.iter("{http://www.opengis.net/kml/2.2}when")]
                points = [gx.text.split(" ") for gx in track.iter("{http://www.google.com/kml/ext/2.2}coord")]
                t = list(zip(times,points))
                print(t)
        for i,point in enumerate(t):
            result.append((point[0],i,point[1][1],point[1][0]))
    df = pd.DataFrame(result, columns=["Date", "Record", "Lat", "Lon"])
    df["Track"] = "Track " + str(index)
    df["Date"] = pd.to_datetime(df["Date"])
    df.replace(np.inf, np.nan, inplace=True)  ## because for some reason, last row speed is calculated as inf
    df = df.dropna()
    print(df.head())
    return df

import pyglet




window = pyglet.window.Window()



@window.event
def on_draw():
    window.clear()
    label.draw()
pyglet.app.run()
exit()

file = filedialog.askdirectory()
basedir = "Z:/SCOTLAND DRIVE 2/Analysis Department/R&D/neil/TfL - Folder Structure/DP0"
for i in range(2,26):
    topDir = basedir + '{0:02d}'.format(int(i))
    folderNumber = '{0:02d}'.format(int(i))
    print(topDir)
    if not os.path.exists(topDir):
        os.makedirs(topDir)
    for path,dirs,files in os.walk(file):
        path = path.replace("\\","/")
        splitpath = path.split("/")

        splitpath = [folderNumber + item[2:] for item in splitpath[7:]]
        print("splitpath is", splitpath)
        #print(path, dirs)
        dirs = [folderNumber + dir[2:] for dir in dirs]
        print(path, dirs)
        targetDir = os.path.join(topDir,*splitpath)
        print("targetdir is",targetDir)
        for dir in dirs:
            if not os.path.exists(targetDir + "/" + dir):
                os.makedirs(targetDir + "/" + dir)




