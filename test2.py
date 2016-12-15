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

def mouseClick(event):
    global x,y
    x = event.x
    y= event.y

def mouseMove(event):
    global x, y,item
    print(event.x-x,event.y-y)
    canvas.move(item,event.x-x,event.y-y)
    x = event.x
    y = event.y

def rollWheel(event):
  global canvas, zoom,mapImage,baseImage,centre,item
  print("event",event.num,event.delta,event)
  if event.delta==120:
    zoom += 100
  elif event.delta==-120:
    zoom-=100
  img = baseImage.resize((zoom,zoom),Image.ANTIALIAS)
  #baseImage.show()
  mapImage = ImageTk.PhotoImage(img)
  canvas.delete(tkinter.ALL)
  item = canvas.create_image(0, 0, image=mapImage, anchor=tkinter.NW)
  x,y=mapMan.get_coords(centre,zoom)
  canvas.create_oval([x - 5, y - 5, x + 5, y + 5], fill="red",width=0)
  print("zoom is",zoom)



f = "S:/SCOTLAND DRIVE 2/JOB FOLDERS/4 - Midlands/3174-MID Hereford Congestion/test p.xlsm"
f1 = "S:/SCOTLAND DRIVE 2/JOB FOLDERS/4 - Midlands/3174-MID Hereford Congestion/test p.xls"
t = "S:/SCOTLAND DRIVE 2/JOB FOLDERS/4 - Midlands/3174-MID Hereford Congestion/frseedrrhjryrud"
#f1 ="C:/Users/NWatson/PycharmProjects/JourneyTimes/blah" + ".xlsm"

fnt = ImageFont.truetype("arial",size = 15)
image = Image.open("map.jpg").convert('RGB')
t = datetime.datetime.strftime(datetime.datetime.now(),"%H:%M:%S")
fnt = ImageFont.truetype("arial", size=18)
drawimage = ImageDraw.Draw(image)
drawimage.rectangle([0,0,100,50],fill="white")
drawimage.text((10,10),text = t,font=fnt,fill="black")
image.save("track " + str(1) + ".jpg")

folder = os.path.dirname(os.path.abspath(__file__))
print(folder)
folder = os.path.join(folder,"Runs\\")
print(folder)
for file in os.listdir(folder):
    file_path = os.path.join(folder,file)
    try:
        if os.path.isfile(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(e)


exit()
win = tkinter.Tk()
canvas = tkinter.Canvas(win)
canvas.pack()
image = Image.open("map.jpg").convert('RGB')
image1 = ImageTk.PhotoImage(image)
drawimage = ImageDraw.Draw(image)
canvas.create_image(0, 0, image = image1, anchor = tkinter.NW)
canvas.create_line(100,100,200,200,width=4)
drawimage.line([100,100,200,200])
drawimage.text((0,0),text="wertoweirtjeroteto",fill="black")
image.save("Runs/poo.jpg")
win.mainloop()