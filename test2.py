import xml.etree.ElementTree as ET
from fastkml import kml
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

l=[[[1560, 883], ['07:30:24', '07:57:19'], [12.84, 12.84]], [[1531, 1832], ['16:15:36', '16:40:41'], [13.890000000000001, 13.890000000000001]], [[1880, 2114], ['06:45:24', '07:04:54'], [17.690000000000001, 17.690000000000001]]]
l = sorted(l,key=lambda x: x[1][0])
s = "07:00:01"

print(datetime.datetime.strftime(datetime.datetime.strptime(s,"%H:%M:%S")+datetime.timedelta(hours=1),"%H:%M:%S"))


