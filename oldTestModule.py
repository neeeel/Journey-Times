import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import bisect
import tkinter
import xml.etree.ElementTree as ET
import MainWindow



import utilities as ut
from scipy import spatial
df = None
file = "S:/SCOTLAND DRIVE 2/JOB FOLDERS/3125-SCO - Enniskillen Traffic Surveys (Atkins)/4.  Analysis/3. Working Data Files/JT/gps3.csv"




def load_timing_points(file):
    tree = ET.parse(file)
    root = tree.getroot()
    print(root.tag)
    lineStrings = tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
    for attributes in lineStrings:
        if "Start" in attributes[0].text:
            print(attributes[0].text, attributes[2][0].text)
        if "End" in attributes[0].text:
            print(attributes[0].text, attributes[2][0].text)
        if "Route" in attributes[0].text:
            print(attributes[0].text, attributes[2][0].text)


def get_timing_points():
    BlueRoute = [(54.32197, -7.64876),(54.32850,-7.65421),(54.33299, -7.66370)]
    tp1 = (54.32197, -7.64876)
    TPEalt = (54.33289, -7.66278)
    tp2 = (54.33299, -7.66370)
    return BlueRoute

def load_csv(file):
    try:
        df = pd.read_csv(file, parse_dates=[1, 2],dtype = {"Latitude":str,"Longitude":str})
        df = df.drop(["Altitude(meter)", "Unnamed: 7", "Record Number"], axis=1)
        l = df.columns.tolist()
        l = ["Date", "Time", "Lat", "Lon", "Speed"]
        df.columns = l
        df.Lat = df.Lat.apply(ut.latTOdddd)
        df.Lon = df.Lon.apply(ut.lonTOdddd)
    except Exception as e:
        print("Tried to load csv file, incorrect format")
        exit()
    return df


def processRoutes():
    global df
    file = "S:/SCOTLAND DRIVE 2/JOB FOLDERS/3125-SCO - Enniskillen Traffic Surveys (Atkins)/4.  Analysis/3. Working Data Files/JT/gps3.csv"
    TimingPoints = []
    df = load_csv(file)
    timingPoints = get_timing_points()
    lats = df["Lat"].tolist()
    lons = df["Lon"].tolist()
    coords = list(zip(lats, lons))
    df["Coords"] = pd.Series(data=coords, dtype=str)
    listOfLists = []
    listOfLists.append(getStartPoints(coords, timingPoints[0], timingPoints[1]))
    listOfLists.append(getEndPoints(coords, timingPoints[0], timingPoints[1]))
    listOfLists.append(getEndPoints(coords, timingPoints[1], timingPoints[2]))
    finalList = []
    for p in zip(*listOfLists):
        l = [df.iloc[s]["Time"].strftime('%H:%M:%S') for s in p]
        print(l)
        finalList.append(l)
    return finalList

def getStartPoints(coords,tpStart,tpEnd):
    global df
    ### for a given set of coordinates, find the point closest to tpStart, where the track is heading away from tpStart towards tpEnd
    tree = spatial.KDTree(coords)
    list = tree.query(np.array([tpStart]), k=100)
    points = np.sort(list[1][0])
    startPoints = []
    index = 0
    while index < len(points):
        temp = [i for i in points[index:] if i < points[index] + 30]
        length = len(temp)

        ## sort the selected timing points with regard to closeness to start point, closest is first
        temp = (sorted([(i, df.iloc[i]["Time"].strftime('%H:%M:%S'),
                         ut.getDist((df.iloc[i]["Lat"], df.iloc[i]["Lon"]), tpStart)) for i in temp],
                       key=lambda x: x[2]))

        ## step through the list of sorted timing points, find the closest point that is also heading away from the start point
        for t in temp:
            i = t[0]
            if ut.getDist((df.iloc[i]["Lat"], df.iloc[i]["Lon"]), tpEnd) >= ut.getDist(
                    (df.iloc[i + 1]["Lat"], df.iloc[i]["Lon"]),
                    tpEnd):  # we have reached start point, and are travelling in direction of end point
                startPoints.append(t[0])
                break
        index += length
    return startPoints

def getEndPoints(coords,tpStart,tpEnd):
    global df
    ### for a given set of coordinates, find the point closest to tpEnd, where the track is heading away from tpStart
    tree = spatial.KDTree(coords)
    list = tree.query(np.array([tpEnd]), k=100)
    points = np.sort(list[1][0])
    endPoints = []
    index = 0
    while index < len(points):
        temp = [i for i in points[index:] if i < points[index] + 30]
        length = len(temp)
        temp = (sorted([(i, df.iloc[i]["Time"].strftime('%H:%M:%S'),
                         ut.getDist((df.iloc[i]["Lat"], df.iloc[i]["Lon"]), tpEnd),df.iloc[i]["Lat"], df.iloc[i]["Lon"]) for i in temp],
                       key=lambda x: x[2]))
        for t in temp:
            i = t[0]
            if ut.getDist((df.iloc[i]["Lat"], df.iloc[i]["Lon"]), tpStart) <= ut.getDist(
                    (df.iloc[i + 1]["Lat"], df.iloc[i]["Lon"]),
                    tpStart):  # we have reached end point , but still travelling away from start point
                endPoints.append(t[0])
                break
        index += length
    return endPoints


threshold = 30  # denotes the min index difference between 2 selected points in order for them to be selected
## eg if we do a closest point search, and get back indexes [25,26,300,320] because 26 is less than 'threshold' away from 25, we would select 26 as a start point, then 300, but 320 is less than
#  'threshold' away from 300, so we would discard 300 and select 320, so our 2 selected start points would be 26,320



#process()
exit()

TimingPoints = []

df = load_csv(file)
timingPoints = get_timing_points()
timingPointStart = timingPoints[0]
timingPointEnd = timingPoints[-1]
lats = df["Lat"].tolist()
lons = df["Lon"].tolist()
coords = list(zip(lats,lons))
df["Coords"] = pd.Series(data=coords,dtype=str )


##get the start indexes of runs from TPStart to TPEnd






listOfLists = []
listOfLists.append(getStartPoints(coords,timingPoints[0],timingPoints[1]))
listOfLists.append(getEndPoints(coords,timingPoints[0],timingPoints[1]))
listOfLists.append(getEndPoints(coords,timingPoints[1],timingPoints[2]))

for p in zip(*listOfLists):
    l = [ df.iloc[s]["Time"].strftime('%H:%M:%S')  for s in p]
    print(l)

print("-------------------------------------------------------------------------------------------------")

exit()
tree = spatial.KDTree(coords)
list = tree.query(np.array([timingPointStart]),k=100)
points = np.sort(list[1][0])
startPoints=[]
index = 0
while index < len(points):
    temp =[i for i in points[index:] if i <points[index] + 30]
    length = len(temp)
    temp = (sorted([(i, df.iloc[i]["Time"].strftime('%H:%M:%S'),ut.getDist((df.iloc[i]["Lat"], df.iloc[i]["Lon"]),timingPointStart )) for i in temp],key=lambda x: x[2]))
    #print(temp)
    #print()
    for t in temp:
        i = t[0]
        if ut.getDist((df.iloc[i]["Lat"], df.iloc[i]["Lon"]),timingPointEnd ) >= ut.getDist((df.iloc[i+1]["Lat"], df.iloc[i]["Lon"]),timingPointEnd):  # we have reached start point, and are travelling in direction of end point
            startPoints.append(t[0])
            break
    index += length

#print(startPoints)
listOfLists = []
for tp in timingPoints[1:]:  ## we are interating through the rest of the timing points ( excluding the first) and finding the closest point to tpEnd that is heading away from TPStart
    timingPointEnd = tp
    timingPointStart = timingPoints[timingPoints.index(tp) - 1]
    print(timingPointStart, timingPointEnd)
    tree = spatial.KDTree(coords)
    list = tree.query(np.array([timingPointEnd]),k=100)
    points = np.sort(list[1][0])
    print("points are ",points)
    endPoints=[]
    index = 0
    while index < len(points):
        temp =[i for i in points[index:] if i <points[index] + 30]
        length = len(temp)
        temp = (sorted([(i, df.iloc[i]["Time"].strftime('%H:%M:%S'), ut.getDist((df.iloc[i]["Lat"], df.iloc[i]["Lon"]),timingPointEnd )) for i in temp],key=lambda x: x[2]))
        print(timingPointStart,timingPointEnd,temp)
        print()
        for t in temp:
            i = t[0]
            if ut.getDist((df.iloc[i]["Lat"], df.iloc[i]["Lon"]),timingPointStart ) <= ut.getDist((df.iloc[i+1]["Lat"], df.iloc[i]["Lon"]),timingPointStart ):  #we have reached end point , but still travelling away from start point
                endPoints.append(t[0])
                break
        index += length
    listOfLists.append(endPoints)

endpoints = listOfLists[-1]
print(len(startPoints),len(endPoints))
if startPoints[-1]>= endPoints[-1]:
    del startPoints[-1]

listOfLists.insert(0,startPoints)
print("list of lists is ",listOfLists)
for p in zip(*listOfLists):
    l = [ df.iloc[s]["Time"].strftime('%H:%M:%S')  for s in p]
    print(l)

exit()



## this list comprehension builds the final run selections, for each value x in startPoints, it finds the first value in endPoints that is higher than x, and pairs it with x

runs =[(x,endPoints[bisect.bisect_left(endPoints, startPoints[i])]) for i,x in enumerate(startPoints)]

print(runs,type(runs))

diff  = [y-x for x,y in runs]
med = float(np.median(diff))
finalRuns = [runs[i] for i,x in enumerate(diff) if x < 4 * med]
print("Final runs are ",finalRuns)

for r in finalRuns:
    s,f = r
    print(df.iloc[s]["Time"].strftime('%H:%M:%S') + " " + df.iloc[f]["Time"].strftime('%H:%M:%S'))


exit()
plt.plot(df["dist"][:5000])
plt.show()