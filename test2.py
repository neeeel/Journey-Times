import xml.etree.ElementTree as ET
from fastkml import kml
#import MainWindow
import datetime
import pandas as pd
import openpyxl
import win32com.client
import pandas as pd
import numpy as np
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


file = "C:/Users/NWatson/Desktop/JT setup example (2).kml"
tree = etree.parse(file)
root = tree.getroot()
#root = etree.Element(root)
print("len",len(root))
print("doc",root.findall(".//{http://www.opengis.net/kml/2.2}Folder"))
children = list(root)
for child in children:
    print(child.tag,child.attrib)