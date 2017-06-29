import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
import bisect
#import xml.etree.ElementTree as ET
import MainWindow
import operator
from tkinter import filedialog,messagebox
import datetime
import math
import utilities as ut
from scipy import spatial
import time


df = None

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

    def add_timing_point(self,lat,long,dir,ID,reorder=False):
        print("adding timing point to route",self.name,"id is",ID,"type of id is ",type(ID))
        if dir == 0:
            dir = "P"
        if dir == 1:
            dir = "S"
        print("adding timing point",lat,long,dir,ID)
        if reorder == True:
            for index,tp in enumerate(self.timingPoints):
                print(tp)
                if tp[1] == dir and tp[0]>= int(ID):
                    self.timingPoints[index] = (tp[0] + 1,dir,tp[2],tp[3])
        self.timingPoints.append((int(ID),dir,float(lat),float(long)))
        self.timingPoints = sorted(self.timingPoints, key=operator.itemgetter(1, 0))
        if not dir in self.dir:
            self.dir.append(dir)
            self.dir = sorted(self.dir)

    def delete_timing_point(self,dir,ID):

        if dir == 0:
            dir = "P"
        if dir == 1:
            dir = "S"
        print("deleting point", dir, ID)
        print("before delete",self.timingPoints)
        self.timingPoints = [tp for  tp in self.timingPoints if not (tp[1] == dir and tp[0] == int(ID))]
        print("after delete", self.timingPoints)
        for index, tp in enumerate(self.timingPoints):
            print(tp)
            if tp[1] == dir and tp[0] > int(ID):
                self.timingPoints[index] = (tp[0] - 1, dir, tp[2], tp[3])

    def save_timing_points(self,file):
        output = [self.name + "/" + tp[1] + "/" + str(tp[0]) + "/" + str(tp[2]) + "," + str(tp[3]) + "\n" for tp in self.timingPoints]
        print("output is",output)
        with open(file,"w") as f:
            f.writelines(output)


    def add_map(self,image):
        self.mapImage = image
        #self.mapImage.show()

    def get_map(self):
        print("size of map",self.mapImage.size)
        return self.mapImage

    def add_track(self,track):
        self.tracks.append(track)

    def adjust_timing_point(self,dir,index,value):
        ###
        ### direction is 0 or 1 , indicating primary or secondary
        ###
        if dir == 0:
            dir = "P"
        else:
            dir = "S"
        tps = [tp for tp in self.timingPoints if tp[1] == dir]
        locationInList = [(tp[0], tp[1]) for tp in self.timingPoints].index((index,dir))
        print("location in list is",locationInList)
        print("previous value is",self.timingPoints[locationInList])
        self.timingPoints[locationInList] = (index,dir,value[0],value[1])
        print("new value is",self.timingPoints[locationInList])

    def check_for_secondary_direction(self):
        if len(self.dir)== 1:
            print("filling in missing direction")
            current = self.dir[0]
            if current == "P":
                dir = "S"
            else:
                dir = "P"
            l = list(reversed(self.timingPoints))
            for index,item in enumerate(l):
                self.add_timing_point(item[2],item[3],dir,index+1)

    def get_timing_points(self):
        TPs = []
        print("stored timing points are",self.timingPoints)
        print(self.dir)
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



def load_gsd(file,index):
    ###
    ### load the GPS data from the GSD file into a pandas dataframe
    ### if theres any sort of error we just abort
    ###

    global df

    if ".gsd" not in file:
        df = None
        messagebox.showinfo("error", "selected file is not a csv,gpx or gsd file")
        return
    try:
        data = pd.read_table(file)
        cleaned_data = []
        for row in data.values.tolist():
            result = parse_gsd(row)
            if not result is None:
                #print(result)
                cleaned_data.append(result)
        df = pd.DataFrame(cleaned_data)
        df.columns = ["Lat", "Lon", "Time"]
        #df["Date"].apply(pd.to_datetime)

        df["Time"].apply(np.datetime64)
        df = df.reset_index(drop=True)
        df.index.name = "Record"
        df.reset_index(inplace=True)
        print(df.head())
        print(df.info())
        #df.to_csv("dumped.csv")
    except PermissionError as e:
        print("couldnt dump data")
    return df

def load_csv(file,index):
    ###
    ### load the GPS data from the CSV file into a pandas dataframe
    ### if theres any sort of error we just abort
    ###

    global df

    if ".csv" not in file:
        df = None
        messagebox.showinfo("error", "selected file is not a csv or gpx file")
        return
    try:
        df = pd.read_csv(file, parse_dates=[[1, 2]],dayfirst=True,dtype = {"Latitude":str,"Longitude":str},usecols = [0,1,2,3,4])
        cols = list(df.columns.values)
        print("column heads",cols)
        if "Altitude(meter)" in cols:
            df = df.drop(["Altitude(meter)"], axis=1)
        if "Unnamed: 7" in cols:
            df = df.drop(["Unnamed: 7"], axis=1)
        l = ["Time","Record", "Lat", "Lon"]
        df.columns = l
        df["Time"] = df["Time"].apply(lambda x: x.replace(microsecond=0))
        #df["Time"] = df["Time"] + pd.DateOffset(hours=1)
        ###
        ### convert the gps data into WSG 84
        ###
        df.Lat =df.Lat.apply(ut.latTOdddd)
        df.Lon = df.Lon.apply(ut.lonTOdddd)
        df["Track"] = "Track " + str(index)
        #df.to_csv("dumped.csv")
    except PermissionError as e:
        print("couldnt dump data")
    except Exception as e:
        messagebox.showinfo("error","Tried to load csv file, incorrect format")
        print("____________________________________________OOPS_____________________________________________________")
        print(e)
        df = None
    return df

def load_gpx(file,index):
    global df
    if ".gpx" not in file:
        df = None
        messagebox.showinfo("error", "selected file is not a gpx file")
        return
    try:
        tree = etree.parse(file)
        root = tree.getroot()
        data = []
        count = 0
        uri = root.tag.replace("gpx","")
        for name in root.iter(uri+"name"):
            print(name.text)
        for track in root.iter(uri + "trk"):
            for seg in track.iter(uri + "trkpt"):
                #print(seg.get("name"))
                lat = float(seg.get("lat"))
                lon = float(seg.get("lon"))
                #print(seg.get("name"))
                point = [count, lat, lon]
                count += 1
                for child in seg:
                    if child.tag == uri + "time":
                        point.insert(0, child.text)
                if len(point) == 3:
                    point.insert(0, np.nan)
                data.append(point)
        df = pd.DataFrame(data)
        l = ["Time", "Record", "Lat", "Lon"]
        df.columns = l
        df["Time"] = pd.to_datetime(df["Time"],dayfirst=True)
        df["Time"] = df["Time"].apply(lambda x:x.replace(microsecond=0))
        df["Track"] = "Track " + str(index)
        df.replace(np.inf, np.nan,inplace=True) ## because for some reason, last row speed is calculated as inf
        df = df.dropna()
    except Exception as e:
        messagebox.showinfo("error", "Tried to load gpx file, incorrect format or corrupted data")
        print("____________________________________________OOPS_____________________________________________________")
        print(e)
        df = None
    print("len of df is",len(df))

    return df

def load_kml(file,index):
    result = []
    routes = {}
    dir = "C:\\user\\nwatson\\desktop\\"
    # file = filedialog.askopenfilename(initialdir=dir)
    if file == "":
        return
    if file[-4:] == ".kml":
        tree = etree.parse(file)
        root = tree.getroot()
        # "root",root.tag)
        # for child in root:
        # print(child.tag,child.attrib)
        doc = root.find("{http://www.opengis.net/kml/2.2}Document")
        if doc is None:
            return
        if doc.find("{http://www.opengis.net/kml/2.2}Folder") is None:
            # print("assigning doc")
            iter = root.iter("{http://www.opengis.net/kml/2.2}Document")
        else:
            # print("assigning folder")
            iter = doc.iter("{http://www.opengis.net/kml/2.2}Folder")
        t = []
        for item in iter:
            tps = []

            for track in item.iter("{http://www.google.com/kml/ext/2.2}Track"):
                times = [when.text for when in track.iter("{http://www.opengis.net/kml/2.2}when")]
                points = [gx.text.split(" ") for gx in track.iter("{http://www.google.com/kml/ext/2.2}coord")]
                t = list(zip(times, points))
                print(t)
        for i, point in enumerate(t):
            result.append((point[0], i, point[1][1], point[1][0]))
    df = pd.DataFrame(result, columns=["Time", "Record", "Lat", "Lon"])
    df["Track"] = "Track " + str(index)
    df["Time"] = pd.to_datetime(df["Time"])
    df["Time"] = df["Time"].apply(lambda x: x.replace(microsecond=0))
    df[["Lat","Lon"]] = df[["Lat","Lon"]].astype(float)
    df.replace(np.inf, np.nan, inplace=True)  ## because for some reason, last row speed is calculated as inf
    df = df.dropna()
    print(df.head())
    return df

def get_date(index):
    ###
    ### returns the date of a given index in the pandas dataframe
    ### returns "" if the index isnt found
    ###
    global df
    if df is None:
        return ""
    try:
        return df.iloc[index]["Time"].strftime("%d/%m/%y")
    except IndexError as e:
        print("Index not found")
        return ""

def load_timing_points():

    routes = {}
    dir = "C:\\user\\nwatson\\desktop\\"
    file = filedialog.askopenfilename(initialdir=dir)
    if file == "":
        return
    if file[-4:] == ".txt":
        with open(file,"r") as f:
            try:
                lines = [line.rstrip('\n') for line in f]
                for line in lines:
                    data = line.split("/")
                    name = data[0].strip()
                    dir = data[1].strip()
                    tpNo = data[2].strip()
                    coords = data[3].strip().replace(" ","")
                    coords = coords.split(",")
                    if name in routes:
                        route = routes[name]
                    else:
                        route = Route(name,dir)
                        routes[name] = route
                    routes[name].add_timing_point(coords[0],coords[1],dir,tpNo)
            except Exception as e:
                messagebox.showinfo("error", "Tried to load Timing points, incorrect format\n " + str(line))


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
        routeName = ""
        timingPoints = []
        for item in iter:
            tps = []
            routeName = item.find("{http://www.opengis.net/kml/2.2}name").text
            print("routename is",routeName)
            try:
                dir = routeName.split("/")[1]
                routeName=routeName.split("/")[0]
                for tp in item.iter("{http://www.opengis.net/kml/2.2}Placemark"):
                    name = tp.find("{http://www.opengis.net/kml/2.2}name").text
                    print("name is",name)
                    if name is not None:
                        ID = int(float(name))
                        tps.append([routeName,dir, ID])

                for i, tp in enumerate(item.iter("{http://www.opengis.net/kml/2.2}coordinates")):
                    data = tp.text.split(",")
                    tps[i].append(data[1])
                    tps[i].append(data[0])

                for tp in tps:
                    timingPoints.append(tp)
            except Exception as e:
                print("error",e)
                messagebox.showinfo("error", "Tried to load Timing points, incorrect format when trying to load\n " \
                                    + str(routeName) + ".\nRoute name should be in the format Route name/Direction\n eg Route 1/N" \
                                    + "\n and each timing point should be numbered in order")
                return


        print(timingPoints)
        for tp in timingPoints:
            if tp[1] == "N" or tp[1] == "E" or tp[1] == "Clockwise":
                dir = "P"
            else:
                dir = "S"
            print(tp)
            if tp[0] in routes:
                route = routes[tp[0]]
            else:
                route = Route(tp[0], dir)
                routes[tp[0]] = route
            routes[tp[0]].add_timing_point(tp[3], tp[4], dir, tp[2])
    for key,value in routes.items():
        print("checking route",key,"for 2 direcdtions")
        routes[key].check_for_secondary_direction()
    return routes

def get_leg_distance(row):
    ###
    ### calculate leg distance for a given row
    ### from the current row to the next row
    ### we have the next rows lat and lon already stored in latNext, lonNext
    ###
    p1 = (row["Lat"],row["Lon"])
    p2 = (row["latNext"],row["lonNext"])
    #print(p1, p2)
    dist = ut.getDistInMiles(p1,p2)
    #print(p1,p2,dist)
    return dist

def get_speed(track):
    ###
    ### takes a list of indexes into the dataframe, specifying where a run hit each timing point
    ### eg [200,400,600]
    ### returns a list [[speeds],[distance]] for the specified track, where speeds is a list of average speeds between
    ### timing points, and the average speed for the whole journey.
    ### distances is a list of distance between each timing point, and distance between first and last timing point
    ### ie total distance
    ###

    global df,window
    units = window.get_units()
    dfTrack = df.iloc[track[0]:track[-1]+1].copy()
    if len(dfTrack)==1:
        return [[0],[0]]
    track = [t -track[0] for t in track] ## reset the indices to start from 0, since we have just made a new copy of the sliced dataframe
    speeds = []
    distances = []
    for i,val in enumerate(track[:-1]):
        d = dfTrack["legDist"].iloc[track[i]:track[i+1]].sum()
        t = (dfTrack["Time"].iloc[track[i+1]] - dfTrack["Time"].iloc[track[i]]).total_seconds() /86400

        if t !=0:
            speed = round(d/(t*24),2)
        else:
            speed =0
        if units ==2:
            speed = round(speed * 1.60934,2)
            d= round(d * 1.60934,2)
        speeds.append(speed)
        distances.append(d)
    ### calculate speed over whole journey
    d = dfTrack["legDist"].iloc[track[0]:track[-1]].sum()
    t = (dfTrack["Time"].iloc[track[-1]] - dfTrack["Time"].iloc[track[0]]).total_seconds()  /86400
    if t!= 0:
        speed = round(d / (t * 24),2)
        if units == 2:
            speed = round(speed * 1.60934,2)
            d = round(d * 1.60934, 2)
    else:
        speed = 0
    speeds.append(speed)
    distances.append(d)
    return [speeds,distances]

def process_single_track(startIndex,endIndex,timingPoints):
    track = [startIndex,endIndex]
    if len(timingPoints) > 2:
        for tp in timingPoints[1:-1]:
            #p = get_closest_point_to_intermediate_point(startIndex,endIndex,tp)
            track.insert(-1,p)
    speeds = get_speed(track)[0]
    l = []
    durations = []
    times = ([df.iloc[s]["Time"].strftime('%H:%M:%S') for s in track])
    if times != []:
        l.append(track)
        l.append(times)
        for j in range(len(times) - 1):
            durations.append(datetime.datetime.strptime(times[j + 1], "%H:%M:%S") - datetime.datetime.strptime(times[j],
                                                                                                      "%H:%M:%S"))

           # print("duration",durations[-1])
        s = sum(durations, datetime.timedelta())
        durations.append(s)
        l.append(durations)
    if l != []:
        l.append(speeds)
    return l

def process_direction(timingPoints):
    ### this function "cuts" up the dataframe into individual tracks for a specific direction
    ### pointsInRoute specifies a rough estimate of how many Data points are in the average run
    ### this is used to group a bunch of selected points into groups that are roughly close to each otehr
    ###


    print("number of legs greater than 1 minute is", len(df[df["legTime"] > 60]),
          df[df["legTime"] > 60].index.values.tolist())
    segments = df[df["legTime"] > 300].index.values.tolist()
    segments.append(len(df) - 1)
    segments.insert(0, 0)
    print("segments are", segments)
    finalList = []
    for i, value in enumerate(segments[:-1]):
        print("processing segment", segments[i] + 1, segments[i + 1])
        trackList = []
        ###
        ### get the rough estimates of starting points for tracks.
        ###
        startList = (getStartPoints(segments[i] + 1, segments[i + 1], timingPoints[0], timingPoints[1]))
        if startList == []:
            continue  ## check the next segment
        print("start list is",startList)
        ### for each start point, follow the track down the road, until we are close to the next timing point
        for pointIndex,point in enumerate(startList):
            #print("checking start point",pointIndex)
            journey = [point]
            tpIndex = 1
            closestPoint = [point,1000]
            while point < segments[i + 1]:
                pointData = df.iloc[point]
                tp = timingPoints[tpIndex]
                dist = ut.getDistInMiles(tp,(pointData["Lat"],pointData["Lon"]))
                if dist < closestPoint[1]:
                    closestPoint[0] = point
                    closestPoint[1] = dist
                #print("point is",point,"dist is",dist,"tp no is",tpIndex,tp)
                if dist <= 0.02:
                    ###
                    ### we have a qualifying point, but there may be a nearby point that is closer
                    ###
                    tempList = [(point + i,ut.getDistInMiles(tp, (df.iloc[point + i]["Lat"], df.iloc[point + i]["Lon"])))for i in range(1, 15)]
                    point = min(tempList, key=lambda t: t[1])[0]
                    journey.append(point)
                    print("journey is",journey)
                    tpIndex += 1
                    if tpIndex == 8:
                        print("WERWER")
                    closestPoint = [point, 1000]
                    if tpIndex >= len(timingPoints):
                        break
                point+=1
            if len(journey) == len(timingPoints):
                ### check that the selected points are in increasing order
                if sorted(journey)==journey:
                    p = get_final_start_point(journey[0], journey[1], timingPoints[0], timingPoints[1])
                    if not p is None:  ## we need the start point to compare to for the previous runs end point
                        del journey[0]
                        journey.insert(0, p)
                    finalList.append(journey)
            else:
                print("Journey failed after ",len(journey),"timing points",tp,closestPoint)
    print("final list is",finalList)
    if len(finalList) > 1:
        for index,journey in enumerate(finalList[:-1]):
            print("journey is",journey)
            print("following journey is",finalList[index+1])
            if journey[-1] == finalList[index+1][-1]:
                ### we are checking to see if two journeys have the same end time
                ### if they do, we want to remove the one that has the earliest start time
                ### because its likely that this point is the end of a previous journey, ie going the wrong way
                trackList.append(finalList[index+1])
            else:
                trackList.append(journey)

        ##
        ### deal with the final journey in finalList
        ###

        if not finalList[-1] in trackList:
                trackList.append(finalList[-1])
    else:
        ### only 1 run, so copy it into tracklist
        trackList = finalList


    print("after filtering for equal end times of journeys, tracklist is",trackList)

    #trackList = finalList
    finalList = []
    distList = []
    discardedList  = []
    for track in trackList:
        ###
        #### get the average speeds
        ###
        result = get_speed(track)
        speeds = result[0]
        l = []
        times = [df.iloc[s]["Time"].strftime('%H:%M:%S') for s in track]


        l.append(track)
        l.append(times)

        l.append(speeds)
        print("final run details", l)
        finalList.append(l)

        ###
        ### get the total distances between TPS and total distance overall
        ###

        # if result[1] != [0]:
        distList.append(result[1])

    finalList = sorted(finalList, key=lambda x: x[1][0])
    if len(distList) != 0:
        distList = [round(sum(i) / len(distList), 3) for i in zip(*distList)]
    return [finalList, distList, discardedList]

def processRoutes(route,fileList):
    ###
    ### we are passed route info ( as a route object) , and want to get the gps data and cut it up, for both directions of
    ### the route
    global df,avLegTime
    timingPoints = [(x[2],x[3]) for x in route.get_timing_points()[0]]
    d1 = 0

    ###
    ### estimate distance travelled between first tp and final tp
    ###
    for i in range(len(timingPoints)-1):
        d1 +=ut.getDist(timingPoints[i], timingPoints[i+1])
    d2 = 0.0003 # rough distance between 2 points when travelling at abuot 40 mph
    pointsInRoute = int(d1/d2) ##rough estimate of how many points will be travelled in 1 route
    print("points in route is",pointsInRoute)
    dataframes=[]
    for index,file in enumerate(fileList):
        if ".csv" in file:
            print("loading csv")
            temp = load_csv(file,index)
        if ".gpx" in file:
            print("loading gpx")
            temp = load_gpx(file,index)
        if ".gsd" in file:
            print("loading gsd")
            temp = load_gsd(file,index)
        if ".kml" in file:
            print("loading kml")
            temp = load_kml(file,index)
        dataframes.append(temp)
    df = pd.concat(dataframes)
    if df is None:
        print("nothing loaded, returning")
        window.display_data(None)
        messagebox.showinfo("error", "Invalid data file,must be .csv or .gpx, or please check format of data")
        return
    df.sort_values(by=["Track","Time"], inplace=True)
    df = df.reset_index(drop=True)
    del df["Record"]
    df.index.name = "Record"
    df.reset_index(inplace=True)

    df["latNext"] = df["Lat"].shift(-1)
    df["lonNext"] = df["Lon"].shift(-1)
    df["timeNext"] = df["Time"].shift(-1)
    df["timeNext"].iloc[-1] = df["Time"].iloc[-1]
    df["latNext"].iloc[-1] = df["Lat"].iloc[-1]
    df["lonNext"].iloc[-1] = df["Lon"].iloc[-1]
    df["legTime"] = df.apply(lambda row: abs((row["timeNext"] - row["Time"]) / np.timedelta64(1, 's')),
                             axis=1)  # / np.timedelta64(1, 's') if I want an int rather than a timedelta , .split("days")[1].strip() if I want a string
    df["legDist"] = df.apply(get_leg_distance, axis=1)
    df["legSpeed"] = df.apply(lambda row: round(
        row["legDist"] * 3600 / int(row["legTime"]) / abs((row["timeNext"] - row["Time"]) / np.timedelta64(1, 's')),
        2) if row["legTime"] != 0 else 0, axis=1)

    result = []
    print("-------------------------primary direction----------------------------------------")
    result.append(process_direction(timingPoints))
    timingPoints = [(x[2], x[3]) for x in route.get_timing_points()[1]]
    print("-------------------------secondary direction----------------------------------------")
    print("timing points for secondary direction are",timingPoints)
    result.append(process_direction(timingPoints))

    try:
        df["OS Grid Reference"] = ""
        df["Name"] = ""
        df["Information"] = ""
        df["Name 2"] = ""
        df["Altitude"] = 0
        df["Proximity"]=0
        df["Symbol name"] = "Dot"
        df["Route or Track name"] = "Track"
        df["Colour name"] = ""
        df.to_csv("dumped.csv",columns=["OS Grid Reference","Lat","Lon","Name","Information","Name 2","Time","Altitude","Proximity","Symbol name","Route or Track name","Colour name"],
                  header = ["OS Grid Reference","Latitude","Longitude","Name","Information","Name 2","Date and Time","Altitude","Proximity","Symbol name","Route or Track name","Colour name"])
        writer = pd.ExcelWriter('Output in POI Coverter Format.xls')
        df.to_excel(writer, sheet_name='Tracks',columns=["OS Grid Reference","Lat","Lon","Name","Information","Name 2","Time","Altitude","Proximity","Symbol name","Route or Track name","Colour name"],
                    header=["OS Grid Reference", "Latitude", "Longitude", "Name", "Information", "Name 2", "Date and Time","Altitude", "Proximity", "Symbol name", "Route or Track name", "Colour name"],index=False)

        writer.save()
    except PermissionError as e:
        pass
    except ValueError as e:
        messagebox.showinfo(message="Couldnt output in POI Converter format, file is too large")
        pass

    window.receive_processed_data(result)

def getTrack(track):
    ###
    ### in: a list of indices into the dataframe df
    ### out: a sliced copy of the dataframe, from track[0] to track[-1]
    ###

    global df
    track= df[track[0]:track[-1]+1].copy()
    return track

def get_full_dataframe():
    global df
    return df

def getStartPoints(dataStart,dataEnd,tpStart,tpEnd):
    ##
    ## gets a list of potential start points for tracks going from tpStart to Tp End
    ## it grabs the closest 500 points to tpStart, groups them together in bundles of similar magnitude ( eg index 300-400, or 2300-2450)
    ## normally we can just take the first point in a grouping as the rough start point
    ## For each bundle, we check to see if the time between first and last is large, if it is, there has probably been a
    ## pause somewhere, so we grab the last point in a grouping, rather than the first.
    ##

    global df,avLegTime

    tempdf = df.iloc[dataStart + 1:dataEnd]
    lats = tempdf["Lat"].tolist()
    lons = tempdf["Lon"].tolist()
    coords = list(zip(lats, lons))
    if len(coords) <= 1:
        return []
    numselections = int(len(coords) / 10)
    if numselections ==0:
        numselections=1
    tree = spatial.KDTree(coords)
    l = tree.query(np.array([tpStart]), k=numselections)
    if numselections > 1:
        points = np.sort(l[1][0])
    else:
        points = np.array([l[1][0]])
    points = sorted(list(set(points)))
    points = [value + dataStart for value in points]
    print("selected points are ", points)
    if points[-1] == len(df):
        del points[-1]
    startPoints = []
    index = 0
    cutOffIndex = 0

    while index < len(points):
        #print("remaining points are",points[index:])
        #print("current index is",index,"lower bound is ",points[index],"upper bound calculated as ",points[index] + (pointsInRoute ))
        temp = []
        for p in points[index:]:
            if temp == []:
                temp.append(p)
            else:
                #print(p,temp[-1],df.iloc[p]["Time"], df.iloc[temp[-1]]["Time"],(df.iloc[p]["Time"] - df.iloc[temp[-1]]["Time"]).total_seconds())#,temp[-1],df.iloc[p]["Time"].total_seconds(), df.iloc[temp[-1]]["Time"]).total_seconds(),df.iloc[p]["Time"].total_seconds() - df.iloc[temp[-1]]["Time"].total_seconds())
                if (df.iloc[p]["Time"] - df.iloc[temp[-1]]["Time"]).total_seconds() <30 and (df.iloc[p]["Time"] - df.iloc[temp[-1]]["Time"]).total_seconds() >=0:
                #if p < temp[-1] + (pointsInRoute/2):
                    temp.append(p)
                else:
                    break
        #temp2 = [i for i in points[index:] if i < points[index] + (pointsInRoute )] # points in route is the guessed number of GPS points between the start and end points. Here we are trying to gather all the "similar" numbers together to be able to determine the start point
        #print("temp is", temp)
        if temp != []:
            length = len(temp)
            ###
            #### what is the span of time between the first and last points in the set. If its large, then there is probably a pause somewhere, and we have picked a false starting point
            ###
            if len(temp) == 1:
                longestLeg=0
            else:
                longestLeg = np.array(df[["legTime"]][temp[0]:temp[-1]].idxmax())[0]
            #print("longest leg is",longestLeg)
            if df["legTime"].iloc[longestLeg] > 30:
                cutOffIndex = longestLeg
            #print("cutoff index is",cutOffIndex,temp)
            while temp[0] <= cutOffIndex:
                del temp[0]
            #print("after dealing with cutoff index, temp is ", temp)

            ## sort the selected timing points with regard to closeness to start point, closest is first

            temp = (sorted([(i, df.iloc[i]["Time"].strftime('%H:%M:%S'),ut.getDist((df.iloc[i]["Lat"], df.iloc[i]["Lon"]), tpStart)) for i in temp],key=lambda x: x[2]))
            #print("sorted temp is",temp)

            ###
            ### check how close the closest point is. If its further away than 0.009 ( a pretty arbitrary pick at the moment)
            ### then we reject it as being too far away from the start point to count as a run start
            ###
            if temp[0][2] <= 0.0009:
                #print("seleceted", temp[0][0])
                startPoints.append((temp[0][0]))
            else:
                pass
                #print("discarded start point",temp[0])
            index += length
        else:
            index+=1
    #print("no of start points determined",len(startPoints))
    return startPoints

def get_final_start_point(startIndex,endIndex,tpStart,tp):
    ###
    ### we have a rough start point, but there may be a better one. Now that we have a definite fix ( or at least, a rough
    ### fix if there are only 2 timing points) on the time the track hits the next timing point, we can look back from that
    ### time, to solidify the start point, since the actual start point must be between the currently selected start point
    ### and the next timing point in the sequence. If we find the furthest point from the next timing point in the sequence
    ### then the actual start point must be between that point and the next timing point.
    ###


    global df
    print("final start point checking", startIndex, endIndex)
    if startIndex == -1 or endIndex == -1:
        return None
    #print("measuring from tp",tp)
    if startIndex < 0:
        startIndex = 0
    if startIndex==endIndex:
        return None
    tempdf = df.iloc[startIndex:endIndex + 1]
    if len(tempdf)<=1:
        return None
    #print("length of slice is",len(tempdf))
    lats = tempdf["Lat"].tolist()
    lons = tempdf["Lon"].tolist()
    coords = list(zip(lats, lons))
    #print("length of coords is",len(coords))
    maxDist = 0
    maxIndex = 0
    latestClosePoint = 0
    if len(coords)<=1:
        return None

    for i,c in enumerate(coords):
        ###
        ### find the latest point between the start point and the next timing point, that goes close to the start point
        ###
        dist = ut.getDistInMiles(c, tpStart)
        if dist < 0.02:
            latestClosePoint = i
    print("latest close point is",latestClosePoint + startIndex)
    ###
    ### move back a bit, we want to check the nearby points to see if one is closer than the currently selected one
    ###
    latestClosePoint-=3
    if latestClosePoint <0:
        latestClosePoint = 0

    ###
    ### get the distances from tpStart of the next 6 points, and select the nearest one
    ###
    data=[[i + latestClosePoint,ut.getDistInMiles(c,tpStart)] for i,c in enumerate(coords[latestClosePoint:latestClosePoint+6])]
    print("data is",data)
    closestPoint = min(data,key=operator.itemgetter(1))
    return(closestPoint[0] + startIndex)




def parse_gsd(row):
    #print(type(row))
    if type(row[0]) == str:
        data = row[0].split(",")
        if len(data) == 6:
            data[0] = data[0][data[0].index("=")+1:]
            data[0] = float(data[0][:2] + "." + data[0][2:])
            if data[1][0] == "-":
                data[1] = float(data[1][:2] + "." + data[1][2:])
            else:
                data[1] = float(data[1][:1] + "." + data[1][1:])
            yr = data[3][-2:]
            mnth = data[3][-4:-2]
            if len(data[3]) == 5:
                day = data[3][0]
            else:
                day = data[3][:2]

            sec = data[2][-2:]
            min = data[2][-4:-2]
            if len(data[2]) == 5:
                hr = data[2][0]
            else:
                hr = data[2][:2]
            return [data[0],data[1],datetime.datetime(int("20" + yr),int(mnth),int(day),int(hr),int(min),int(sec),0,None)]
        return None



file = "C:/Users/NWatson/Desktop/3360-WAL Bridgewater JT/Journey Time Routes/Route 1(2).gsd"
#load_gsd(file)
#exit()

#print(df.head())
#print(df.iloc[92]["Time"] - df.iloc[91]["Time"])
#if (df.iloc[92]["Time"] - df.iloc[91]["Time"]).total_seconds() > 10:
    #print("oh phoo")
#else:
    #print("hurrah")
#print(df.info())
#mask = df["legSpeed"] == np.inf
#print(df[mask])
#exit()

window = MainWindow.mainWindow()
window.setCallbackFunction("process",processRoutes)
window.setCallbackFunction("Routes",load_timing_points)
window.setCallbackFunction("getTrack",getTrack)
window.setCallbackFunction("getSpeed",get_speed)
window.setCallbackFunction("getDate",get_date)
window.setCallbackFunction("singleTrack",process_single_track)
window.setCallbackFunction("fullDataframe",get_full_dataframe)
window.setCallbackFunction("getFullTracks",lambda : df)
window.mainloop()
del df


