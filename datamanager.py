import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
import bisect
#import xml.etree.ElementTree as ET
import MainWindow
import mainwindow2
import operator
from tkinter import filedialog,messagebox
import datetime
import math
import utilities as ut
from scipy import spatial
import time
import dragandzoomcanvas

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
            #print("routename is",routeName)
            try:
                dir = routeName.split("/")[1]
                routeName=routeName.split("/")[0]
                for tp in item.iter("{http://www.opengis.net/kml/2.2}Placemark"):
                    name = tp.find("{http://www.opengis.net/kml/2.2}name").text
                    #print("name is",name)
                    if name is not None:
                        ID = int(name)
                        tps.append([routeName,dir, ID])

                for i, tp in enumerate(item.iter("{http://www.opengis.net/kml/2.2}coordinates")):
                    data = tp.text.split(",")
                    tps[i].append(data[1])
                    tps[i].append(data[0])

                for tp in tps:
                    timingPoints.append(tp)
            except Exception as e:
                messagebox.showinfo("error", "Tried to load Timing points, incorrect format when trying to load\n " \
                                    + str(routeName) + ".\nRoute name should be in the format Route name/Direction\n eg Route 1/N" \
                                    + "\n and each timing point should be numbered in order")
                return


        #print(timingPoints)
        for tp in timingPoints:
            #print(tp)
            if tp[0] in routes:
                route = routes[tp[0]]
            else:
                route = Route(tp[0], tp[1])
                routes[tp[0]] = route
            routes[tp[0]].add_timing_point(tp[3], tp[4], tp[1], tp[2])
    return routes

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
        #print("column heads",cols)
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

def get_leg_distance(row):
    ###
    ### calculate leg distance for a given row
    ### from the current row to the next row
    ### we have the next rows lat and lon already stored in latNext, lonNext
    ###
    p1 = (row["Lat"],row["Lon"])
    p2 = (row["latNext"],row["lonNext"])
    dist = ut.getDistInMiles(p1,p2)
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

def getStartPoints(dataStart,dataEnd,tpStart,tpEnd,pointsInRoute):
    ##
    ## gets a list of potential start points for tracks going from tpStart to Tp End
    ## it grabs the closest 500 points to tpStart, groups them together in bundles of similar magnitude ( eg index 300-400, or 2300-2450)
    ## normally we can just take the first point in a grouping as the rough start point
    ## For each bundle, we check to see if the time between first and last is large, if it is, there has probably been a
    ## pause somewhere, so we grab the last point in a grouping, rather than the first.
    ##

    global df,avLegTime

    tempdf = df.iloc[dataStart + 1:dataEnd]
    coords = tempdf[["Lat","Lon"]].values.tolist()
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
        return points
    startPoints = []
    index = 0
    cutOffIndex = 0
    while index < len(points):
        temp = []
        for p in points[index:]:
            if temp == []:
                temp.append(p)
            else:
                if (df.iloc[p]["Time"] - df.iloc[temp[-1]]["Time"]).total_seconds() <30 and (df.iloc[p]["Time"] - df.iloc[temp[-1]]["Time"]).total_seconds() >=0:
                    temp.append(p)
                else:
                    break
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
            print("list comp method",[t for t in temp if t > cutOffIndex])
            while temp[0] <= cutOffIndex:
                del temp[0]
            print("other method",temp)


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
            index += length
        else:
            index+=1
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
    maxIndex = 0
    latestClosePoint = 0
    if len(coords)<=1:
        return None

    for i,c in enumerate(coords):
        ###
        ### find the latest point between the start point and the next timing point, that goes close to the start point
        ###
        dist = ut.getDistInMiles(c, tpStart)
        if dist < 0.01:
            latestClosePoint = i
    print("point with max dist from tp is ",startIndex + maxIndex)
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

def process_direction_alternative(timingPoints):
    ### this function "cuts" up the dataframe into individual tracks for a specific direction
    ### by traversing along the track and determining when it gets close to a timing point
    ###

    ###
    ### segments are parts of the route split by legs that have a long time value. this is because there may be multiple tracks which span days
    ###
    segments = df[df["legTime"] > 300].index.values.tolist()
    segments.append(len(df) - 1)
    segments.insert(0, 0)
    print("segments are", segments)
    journeyList = []
    for i, value in enumerate(segments[:-1]):
        print("processing segment", segments[i] + 1, segments[i + 1])
        trackList = []
        ###
        ### get the rough estimates of starting points for tracks.
        ###
        startList = getStartPoints(segments[i] + 1, segments[i + 1], timingPoints[0], timingPoints[1])
        if startList == []:
            continue  ## check the next segment
        print("start list is", startList)
        ### for each start point, follow the track down the road, until we are close to the next timing point
        for pointIndex, point in enumerate(startList):
            journey = [point]
            tpIndex = 1
            closestPoint = [point, 1000]
            while point < segments[i + 1]:
                pointData = df.iloc[point]
                dist = ut.getDistInMiles(timingPoints[tpIndex], (pointData["Lat"], pointData["Lon"]))
                if dist < closestPoint[1]:
                    closestPoint = [point,dist]
                if dist <= 0.02:
                    journey.append(point)
                    print("journey is", journey)
                    tpIndex += 1
                    closestPoint = [point, 1000]
                    if tpIndex >= len(timingPoints):
                        break
                point += 1
            if len(journey) == len(timingPoints):
                ### check that the selected points are in increasing order
                if sorted(journey) == journey:
                    p = get_final_start_point(journey[0], journey[1], timingPoints[0], timingPoints[1])
                    if not p is None:  ## we need the start point to compare to for the previous runs end point
                        del journey[0]
                        journey.insert(0, p)
                        journeyList.append(journey)
            else:
                print("Journey failed after ", len(journey), "timing points", closestPoint)
    print("journeyList list is", journeyList)
    if len(journeyList) > 1:
        for index, journey in enumerate(journeyList[:-1]):
            if journey[-1] == journeyList[index + 1][-1]:
                ### we are checking to see if two journeys have the same end time
                ### if they do, we want to remove the one that has the earliest start time
                ### because its likely that this point is the end of a previous journey, ie going the wrong way
                trackList.append(journeyList[index + 1])
            else:
                trackList.append(journey)

        ##
        ### deal with the final journey in finalList
        ###

        if not journeyList[-1] in trackList:
            trackList.append(journeyList[-1])
    else:
        ### only 1 run, so copy it into tracklist
        trackList = journeyList

    print("after filtering for equal end times of journeys, tracklist is", trackList)

    # trackList = finalList
    finalList = []
    distList = []
    discardedList = []
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
        #window.display_data(None)
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
    df["legTime"] = df.apply(lambda row: abs((row["timeNext"] - row["Time"]) / np.timedelta64(1, 's')),axis=1)  # / np.timedelta64(1, 's') if I want an int rather than a timedelta , .split("days")[1].strip() if I want a string

    df["legDist"] = df.apply(get_leg_distance, axis=1)

    df["legSpeed"] = df.apply(lambda row: round(
        row["legDist"] * 3600 / int(row["legTime"]) / abs((row["timeNext"] - row["Time"]) / np.timedelta64(1, 's')),
        2) if row["legTime"] != 0 else 0, axis=1)


    coords = df[["Lat","Lon"]].values.tolist()
    print("coords are")

    result = []

    print("-------------------------primary direction----------------------------------------")
    #result.append(process_direction(timingPoints, pointsInRoute, coords))
    result.append(process_direction_alternative(timingPoints))
    timingPoints = [(x[2], x[3]) for x in route.get_timing_points()[1]]

    print("-------------------------secondary direction----------------------------------------")
    print("timing points for secondary direction are",timingPoints)
    #result.append(process_direction(timingPoints, pointsInRoute, coords))
    result.append(process_direction_alternative(timingPoints))
    ### alternative method



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


window = mainwindow2.mainWindow()
window.setCallbackFunction("process",processRoutes)
window.setCallbackFunction("Routes",load_timing_points)
#window.setCallbackFunction("getTrack",getTrack)
window.setCallbackFunction("getSpeed",get_speed)
#window.setCallbackFunction("getDate",get_date)
#window.setCallbackFunction("singleTrack",process_single_track)
window.mainloop()
del df
