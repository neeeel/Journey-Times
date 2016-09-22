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

    def add_timing_point(self,lat,long,dir,ID):
        self.timingPoints.append((ID,dir,float(lat),float(long)))
        self.timingPoints = sorted(self.timingPoints, key=operator.itemgetter(1, 0))
        if not dir in self.dir:
            self.dir.append(dir)

    def add_map(self,image):
        self.mapImage = image
        #self.mapImage.show()

    def get_map(self):
        return self.mapImage

    def add_track(self,track):
        self.tracks.append(track)

    def get_timing_points(self):
        TPs = []
        print(self.dir)
        for d in self.dir:
            l = [tp for tp in self.timingPoints if tp[1] == d]
            l =sorted(l,key=lambda x: x[0])
            TPs.append(l)
        if len(self.dir) == 1:
            reverse = list(reversed(TPs[0]))
            TPs.append(reverse)
        return TPs

    def display(self):
        print(self.name)
        print("---------------------------")
        for tp in self.timingPoints:
            print(tp[0],tp[1]," : ",tp[2],tp[3])

def load_csv(file):
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
        df = pd.read_csv(file, parse_dates=[[1, 2]],dtype = {"Latitude":str,"Longitude":str},usecols = [0,1,2,3,4])
        cols = list(df.columns.values)
        print("column heads",cols)
        if "Altitude(meter)" in cols:
            df = df.drop(["Altitude(meter)"], axis=1)
        if "Unnamed: 7" in cols:
            df = df.drop(["Unnamed: 7"], axis=1)
        l = ["Time","Record", "Lat", "Lon"]
        df.columns = l
        df.Lat = df.Lat.apply(ut.latTOdddd)
        df.Lon = df.Lon.apply(ut.lonTOdddd)
        #df.drop_duplicates(["Time"],keep="first",inplace=True)
        df["latNext"] = df["Lat"].shift(-1)
        df["lonNext"] = df["Lon"].shift(-1)
        df["timeNext"] = df["Time"].shift(-1)
        df["timeNext"].iloc[-1] = df["Time"].iloc[-1]
        df["latNext"].iloc[-1] = df["Lat"].iloc[-1]
        df["lonNext"].iloc[-1] = df["Lon"].iloc[-1]
        df["legTime"] = df.apply(lambda row: abs((row["timeNext"] -  row["Time"])/ np.timedelta64(1, 's')) ,axis = 1) # / np.timedelta64(1, 's') if I want an int rather than a timedelta , .split("days")[1].strip() if I want a string
        df["legDist"] = df.apply(get_leg_distance,axis=1)
        print("converting leg speeds")
        df["legSpeed"] = df.apply(lambda row: round(row["legDist"]*3600/int(row["legTime"]) /abs((row["timeNext"] -  row["Time"])/ np.timedelta64(1, 's')),2) if row["legTime"] != 0 else 0,axis =1)
    except Exception as e:
        messagebox.showinfo("error","Tried to load csv file, incorrect format")
        print("____________________________________________OOPS_____________________________________________________")
        print(e)
        df = None
    print(df.loc[df["legSpeed"] == -13.8])
    return df

def load_gpx(file):
    global df
    if ".gpx" not in file:
        df = None
        messagebox.showinfo("error", "selected file is not a csv or gpx file")
        return
    try:
        tree = ET.parse(file)
        root = tree.getroot()

        data = []
        count = 0
        for track in root.iter("{http://www.topografix.com/GPX/1/1}trk"):
            for seg in track.iter("{http://www.topografix.com/GPX/1/1}trkpt"):
                point = []
                lat = float(seg.get("lat"))
                lon = float(seg.get("lon"))
                point = [count, lat, lon]
                count += 1
                for child in seg:
                    if child.tag == "{http://www.topografix.com/GPX/1/1}time":
                        point.insert(0, child.text)
                if len(point) == 3:
                    point.insert(0, np.nan)
                data.append(point)
        df = pd.DataFrame(data)
        print(list(df.columns.values))
        l = ["Time", "Record", "Lat", "Lon"]
        df.columns = l


        #df.Lat = df.Lat.apply(ut.latTOdddd)
        #df.Lon = df.Lon.apply(ut.lonTOdddd)
        #df["Time"].drop_duplicates(keep="first", inplace=True)
        df["latNext"] = df["Lat"].shift(-1)
        df["lonNext"] = df["Lon"].shift(-1)
        df = df.dropna()

        df["Time"] = pd.to_datetime(df["Time"])
        df["timeNext"] = df["Time"].shift(-1)
        df["timeNext"].iloc[-1] = df["Time"].iloc[-1]

        df["legTime"] = df.apply(lambda row: abs((row["timeNext"] - row["Time"]) / np.timedelta64(1, 's')),
                                 axis=1)  # / np.timedelta64(1, 's') if I want an int rather than a timedelta , .split("days")[1].strip() if I want a string
        df["legDist"] = df.apply(get_leg_distance, axis=1)
        df["legSpeed"] = df.apply(
            lambda row: round(row["legDist"] * 3600 / abs((row["timeNext"] - row["Time"]) / np.timedelta64(1, 's')), 2),
            axis=1)
        df.replace(np.inf, np.nan,inplace=True) ## because for some reason, last row speed is calculated as inf
        df = df.reset_index(drop=True)
    except Exception as e:
        messagebox.showinfo("error", "Tried to load gpx file, incorrect format or corrupted data")
        print("____________________________________________OOPS_____________________________________________________")
        print(e)
        df = None
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
        print("root",root.tag)
        for child in root:
            print(child.tag,child.attrib)
        doc = root.find("{http://www.opengis.net/kml/2.2}Document")
        if doc is None:
            return
        if doc.find("{http://www.opengis.net/kml/2.2}Folder") is None:
            print("assigning doc")
            iter = root.iter("{http://www.opengis.net/kml/2.2}Document")
        else:
            print("assigning folder")
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


        print(timingPoints)
        for tp in timingPoints:
            print(tp)
            if tp[0] in routes:
                route = routes[tp[0]]
            else:
                route = Route(tp[0], tp[1])
                routes[tp[0]] = route
            routes[tp[0]].add_timing_point(tp[3], tp[4], tp[1], tp[2])
    return routes

def get_leg_distance(row):
    ###
    ### calculate leg distance for a given row
    ### from the current row to the next row
    ### we have the next rows lat and lon already stored in latNext, lonNext
    ###
    p1 = (row["Lat"],row["Lon"])
    p2 = (row["latNext"],row["lonNext"])
    dist = ut.getDistInMiles(p1,p2)
    #print(p1,p2,dist)
    return dist

def get_speed(track):
    global df
    print("original track is",track)
    dfTrack = df.iloc[track[0]:track[-1]+1].copy()
    track = [t -track[0] for t in track] ## reset the indices to start from 0, since we have just made a new copy of the sliced dataframe
    #dfTrack["legDist"] = dfTrack.apply(get_leg_distance, axis=1)
    speeds = []
    print("in get speed, track is ",track)
    for i,val in enumerate(track[:-1]):
        print("processing",i,val)
        print(track[i],track[i+1])
        d = dfTrack["legDist"].iloc[track[i]:track[i+1]].sum()
        print("in get speed,times are", dfTrack["Time"].iloc[track[i]])
        print("in get speed,times are",dfTrack["Time"].iloc[track[i+1]])
        t = (dfTrack["Time"].iloc[track[i+1]] - dfTrack["Time"].iloc[track[i]]).total_seconds() /86400
        if t !=0:
            speed = round(d/(t*24),2)
        else:
            speed =0
        speeds.append(speed)

    ### calculate speed over whole journey
    d = dfTrack["legDist"].iloc[track[0]:track[-1]].sum()
    t = (dfTrack["Time"].iloc[track[-1]] - dfTrack["Time"].iloc[track[0]]).total_seconds()  /86400
    speed = round(d / (t * 24),2)
    speeds.append(speed)
    return speeds

def get_num_points(tp1,tp2):
    global df
    d1 = 0
    ## estimate distance travelled between first tp and final tp
    d1 += ut.getDist(tp1, tp2)
    d2 = 0.0003  # rough distance between 2 points when travelling at abuot 40 mph
    pointsInRoute = int(d1 / d2)  ##rough estimate of how many points will be travelled in 1 route
    avSpeed = df["legSpeed"].mean()
    print("average speed over dataframe is", avSpeed)
    print("rough no of points is", pointsInRoute)
    if avSpeed != 0:
        print("new calculation of points in route is ", int(d1 / (d2 * (avSpeed / 40))))
        pointsInRoute = int(
            d1 / (d2 * (avSpeed / 40)))  #### because we need a fairly accurate estimation of points in route,
        ### so we get average speed, and mutliply avspeed/40 to scale the distance per leg
    return pointsInRoute

def process_single_track(startIndex,endIndex,timingPoints):
    track = [startIndex,endIndex]
    if len(timingPoints) > 2:
        for tp in timingPoints[1:-1]:
            p = get_closest_point_to_intermediate_point(startIndex,endIndex,tp)
            track.insert(-1,p)
    speeds = get_speed(track)
    l = []
    durations = []
    times = ([df.iloc[s]["Time"].strftime('%H:%M:%S') for s in track])
    if times != []:
        l.append(track)
        l.append(times)
        for j in range(len(times) - 1):
            durations.append(datetime.datetime.strptime(times[j + 1], "%H:%M:%S") - datetime.datetime.strptime(times[j],
                                                                                                      "%H:%M:%S"))

            print("duration",durations[-1])
        s = sum(durations, datetime.timedelta())
        durations.append(s)
        l.append(durations)
    if l != []:
        l.append(speeds)
    return l

def process_direction(timingPoints,pointsInRoute,coords):

    ### this function "cuts" up the dataframe into individual tracks for a specific direction
    ### pointsInRoute specifies a rough estimate of how many Data points are in the average run
    ### this is used to group a bunch of selected points into groups that are roughly close to each otehr
    ###

    trackList = []

    ###
    ### get the rough estimates of starting points for tracks.
    ###
    startList = (getStartPoints(coords, timingPoints[0], timingPoints[1], pointsInRoute))
    print("startlis is",startList)
    if startList == []:
        print("no start list")
        return [[],[],[]]

    ###
    ### get the rough estimate for the end point for a route. We know the end point must be between start point x
    ### and startpoint x+ 1, so we use this to search
    for i in range(len(startList[:-1])):
        ep = get_temp_end_point(startList[i],startList[i+1],timingPoints[-1])
        if ep is None: ### we get back None if there was a problem finding the end point for some reason
            pass
        else:
            track= [startList[i],ep]
            trackList.append(track)

    ###
    ### deal with the last selected start point, by searching to the end of the dataframe df
    ###
    ep = get_temp_end_point(startList[-1],len(df)-1,timingPoints[-1])
    if ep is None:
        pass
    else:
        track=[startList[-1],ep]
        trackList.append(track)

    #if trackList = []
    print("after initial stage, tracklist is",trackList)
    ###
    ### deal with the intermediate timing points, if any, between the start and end point. This is simple
    ### we know that there can only be 1 closest point between the estimated start and end points
    ###
    for tp in timingPoints[1:-1]:
        for t in trackList:
            if t[-1] > t[0]:
                p = get_closest_point_to_intermediate_point(t[0], t[-1] , tp)
                t.insert(-1,p)

    ###
    ### our start and end points are just estimates, which we can use to get a fixed index for intermediate timing
    ### points. We can then use the fixed points to solidify our start and end points
    ###
    for t in trackList:
        p = get_final_end_point(t[-2],t[-1],timingPoints[-2],timingPoints[-1])
        del t[-1]
        t.append(p)
        p = get_final_start_point(t[0],t[1],timingPoints[0],timingPoints[1])
        del t[0]
        t.insert(0,p)

    ###
    ### build up the data for display in the window
    ###
    print("after clarification stage, tracklist is",trackList)
    removeList = []
    for index,l in enumerate(trackList):
        print(l)
        minVal = min([l[i + 1] - l[i] for i, item in enumerate(l[:-1])])
        if minVal < 2:
            removeList.append(index)




    finalList = []
    distList = []
    for track in trackList:
        ###
        #### get the average speeds
        ###
        speeds = get_speed(track)
        l = []
        times = ([df.iloc[s]["Time"].strftime('%H:%M:%S') for s in track if track[-1] - track[
            0] < 6 * pointsInRoute])  # if the route is shorter than X times pointsInRoute, we keep it, otherwise, we discard it, because its probably a fake route
        if times != []:
            l.append(track)
            l.append(times)
        if l != []:
            l.append(speeds)
            finalList.append(l)
        ###
        ### get the total distances between TPS and total distance overall
        ###
        trackDists = []
        for i, t in enumerate(track[:-1]):
            # print(track[0][i],track[0][i+1],"offset is",offset)
            # print("dist between tps is",self.trackData["legDist"][self.trackList[0][i]-offset:self.trackList[0][i+1]-offset].sum())
            trackDists.append(df["legDist"][ track[i]:track [i + 1]].sum())
        trackDists.append(df["legDist"][track[0]:track[-1]].sum())
        distList.append(trackDists)

    print("track list at end is",finalList)
    print("*" * 20)
    for l in finalList:
        print(l)
        #print("trackduists",trackDists,"distlist",distList)
    if len(distList) !=0:
        distList = [round(sum(i)/len(distList),3) for i in zip(*distList)]


    discardedList = []  #
    print("to be removed", removeList)
    for index in reversed(removeList):
        if len(finalList)> index: ## we might have discarded some runs earlier, if they are 6x longer than average route
            ### so we need to check that the index applies here
            discardedList.append(finalList[index])
            del finalList[index]


    return [finalList,distList,discardedList]

def processRoutes(route,file):
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

    if ".csv" in file:
        print("loading csv")
        df = load_csv(file)
    if ".gpx" in file:
        print("loading gpx")
        df = load_gpx(file)
    if df is None:
        print("nothing loaded, returning")
        window.display_data(None)
        messagebox.showinfo("error", "Invalid data file,must be .csv or .gpx, or please check format of data")
        return
    print("length of df is",len(df))
    avSpeed = df["legSpeed"].mean()
    avLegTime = df["legTime"].median()
    print("average speed is",avSpeed,"av leg time is",avLegTime)
    print("rough no of points is",pointsInRoute)
    #if avSpeed!=0:
        #print("new calculation of points in route is ",int(d1/(d2*avLegTime*(avSpeed/40))))
        #pointsInRoute = int(d1/(d2*avLegTime*(avSpeed/40))) #### because we need a fairly accurate estimation of points in route,
                                                 ### so we get average speed, and mutliply avspeed/40 to scale the distance per leg
    lats = df["Lat"].tolist()
    lons = df["Lon"].tolist()
    coords = list(zip(lats, lons))
    df["Coords"] = pd.Series(data=coords, dtype=str)
    result = []
    result.append(process_direction(timingPoints,pointsInRoute,coords))
    timingPoints = [(x[2], x[3]) for x in route.get_timing_points()[1]]
    result.append(process_direction(timingPoints, pointsInRoute, coords))
    window.receive_processed_data(result)

def getTrack(track):
    ###
    ### in: a list of indices into the dataframe df
    ### out: a sliced copy of the dataframe, from track[0] to track[-1]
    ###

    global df
    track= df[track[0]:track[-1]+1].copy()
    return track

def getStartPoints(coords,tpStart,tpEnd,pointsInRoute):
    ##
    ## gets a list of potential start points for tracks going from tpStart to Tp End
    ## it grabs the closest 500 points to tpStart, groups them together in bundles of similar magnitude ( eg index 300-400, or 2300-2450)
    ## normally we can just take the first point in a grouping as the rough start point
    ## For each bundle, we check to see if the time between first and last is large, if it is, there has probably been a
    ## pause somewhere, so we grab the last point in a grouping, rather than the first.
    ##

    global df,avLegTime
    tree = spatial.KDTree(coords)
    list = tree.query(np.array([tpStart]), k=400)
    points = np.sort(list[1][0])
    print("looking at",tpStart,tpEnd)
    print("selected points are ", points)
    startPoints = []
    index = 0
    cutOffIndex = 0
    while index < len(points):
        print("remaining points are",points[index:])
        print("current index is",index,"lower bound is ",points[index],"upper bound calculated as ",points[index] + (pointsInRoute ))
        temp = [i for i in points[index:] if i < points[index] + (pointsInRoute )] # points in route is the guessed number of GPS points between the start and end points. Here we are trying to gather all the "similar" numbers together to be able to determine the start point
       # print("temp is", temp)
        if temp != []:
            length = len(temp)
            ###
            #### what is the span of time between the first and last points in the set. If its large, then there is probably a pause somewhere, and we have picked a false starting point
            ###
            if len(temp) == 1:
                longestLeg = 0
            else:
                longestLeg = np.array(df[["legTime"]][temp[0]:temp[-1]].idxmax())[0]
            if df["legTime"].iloc[longestLeg] > 20:
                cutOffIndex = longestLeg

            while temp[0] < cutOffIndex:
                del temp[0]
            #print("after dealing with cutoff index, temp is ", temp)

            ## sort the selected timing points with regard to closeness to start point, closest is first

            temp = (sorted([(i, df.iloc[i]["Time"].strftime('%H:%M:%S'),
                             ut.getDist((df.iloc[i]["Lat"], df.iloc[i]["Lon"]), tpStart)) for i in temp],
                           key=lambda x: x[2]))
            print("sorted temp is",temp)
            ###
            ### check how close the closest point is. If its further away than 0.009 ( a pretty arbitrary pick at the moment)
            ### then we reject it as being too far away from the start point to count as a run start
            ###
            if temp[0][2] < 0.009:
                print("seleceted", temp[0][0])
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
    print("measuring from tp",tp)
    if startIndex < 0:
        startIndex = 0
    tempdf = df.iloc[startIndex:endIndex + 1]
    print("length of slice is",len(tempdf))
    lats = tempdf["Lat"].tolist()
    lons = tempdf["Lon"].tolist()
    coords = list(zip(lats, lons))
    print("length of coords is",len(coords))
    maxDist = 0
    maxIndex = 0

    ###
    ### step through all the coords in the selected data set, and find the point furthest from timingpoint tp
    ###
    for i,c in enumerate(coords):
        dist = ut.getDistInMiles(c,tp)
        print("index",i,"dist",dist,c)
        if dist > maxDist:
            maxDist = dist
            maxIndex = i


    print("point with max dist from tp is ",startIndex + maxIndex)
    print("length of reduced coords is", len(coords[maxIndex:]))

    ### restrict the data set to be between maxIndex and the end, because we know that the correct starting point cant
    ### be further back ( in time) than the point that is furthest from tp, and then search the restricted data set
    ### for the point nearest to tpStart
    ### maybe a big assumption, because the track could bend in a wierd way which would allow the closest point to be
    ### before the furthest point away
    ###

    tree = spatial.KDTree(coords[maxIndex:])
    result = tree.query(np.array(tpStart), 1)
    print("final start point result is ", result[1] + startIndex + maxIndex,"adjusted from",startIndex)
    return result[1] + startIndex + maxIndex

def get_closest_point_to_intermediate_point(startIndex,endIndex,tp):
    ###
    ### its simple to get the closest point to the intermediate TPS ( the points that arent the start or end point)
    ### because we already have a rough start point and rough end point, we can just take the closest point to the intermediate
    ### point that falls between the start point and end point.
    ###

    global df
    print("cjecking",startIndex,endIndex,tp)
    tempdf = df.iloc[startIndex:endIndex]
    lats = tempdf["Lat"].tolist()
    lons = tempdf["Lon"].tolist()
    coords = list(zip(lats, lons))
    tree = spatial.KDTree(coords)
    result = tree.query(np.array(tp), 1)
    print("result is ", result[1] + startIndex)
    return result[1] + startIndex

def get_temp_end_point(startIndex,endIndex,tpEnd):
    global df,avLegTime
    print("temp end point checking",startIndex,endIndex)
    print("tpend is",tpEnd)
    cutOffIndex = endIndex

    ###
    ### we want to make sure that there are no breaks or long pauses somewhere in this restricted data set
    ### so we find the time difference between startIndex and endIndex. If its too long, we find the leg with the
    ### longest leg time, this is where the break or pause occurred. We know that the end point of the track, if there
    ### is one, must be before the break, so we restrict the data set further and search between startIndex and
    ### cutoffIndex to find the point closest to tpEnd
    ###

    diff = (
    datetime.datetime.strptime(df.iloc[endIndex]["Time"].strftime('%H:%M:%S'), "%H:%M:%S") -
    datetime.datetime.strptime(df.iloc[startIndex]["Time"].strftime('%H:%M:%S'), "%H:%M:%S")).total_seconds()
    print("diff is",diff)
    longestLeg = np.array(df[["legTime"]][startIndex:endIndex].idxmax())[0]
    if df["legTime"].iloc[longestLeg] > 20:
        cutOffIndex = longestLeg
        print("setting cut off index to ", cutOffIndex)
    tempdf = df.iloc[startIndex:cutOffIndex + 1]
    lats = tempdf["Lat"].tolist()
    lons = tempdf["Lon"].tolist()
    coords = list(zip(lats, lons))
    tree = spatial.KDTree(coords)
    result = tree.query(np.array(tpEnd), 5)
    if result == []:
        print("no results")
        return None
    print("result is",result)
    indexes = list(result[1])
    i = indexes.index(min(indexes))
    print("min value", min(indexes), "index", indexes.index(min(indexes)))
    if result[0][i] < 0.009:
        print("temp selected end point is ",result[1][i])
        print(df.iloc[result[1][i] + startIndex])
        return result[1][i] + startIndex
    return None
    print("determined end point as ",tempdf.iloc[result])

def get_final_end_point(startIndex,endIndex,tp,tpEnd):
    global df
    ###
    ### similar to finding the final start point, we find the final end point by finding the furthest point away from
    ### the 2nd last timing point, and working back from there to find the closest point to the end TP
    ###

    print("end point checking", startIndex, endIndex)
    tempdf = df.iloc[startIndex:endIndex+1]
    lats = tempdf["Lat"].tolist()
    lons = tempdf["Lon"].tolist()
    coords = list(zip(lats, lons))
    maxDist = 0
    minDist = 0
    maxIndex = 0
    tpBearing = ut.get_bearing(tp, tpEnd)
    if tpBearing == 0:
        tpBearing = 0.1
    for i,c in enumerate(coords):
        dist = ut.getDistInMiles(c,tp)
        currentPointBearing = ut.get_bearing(tp,c)
        diff = tpBearing - currentPointBearing
        if dist > maxDist and abs(diff) < 45 :
            maxDist = dist
            maxIndex = i
    print("point with max dist from tp is ",startIndex + maxIndex)
    tree = spatial.KDTree(coords[:maxIndex + 1])
    result = tree.query(np.array(tpEnd), 1)
    print("final end point result is ", result[1] + startIndex,"adjusted from",endIndex)
    return result[1] + startIndex
    # print("determined end point as ",tempdf.iloc[result])





#file = "C:/Users/NWatson/Desktop/Test Data/alternate data gpx/Route 4 LON03 Thaha.gpx"
#df = load_gpx(file)
#print(df.iloc[91])
#print(df.info())
#mask = df["legSpeed"] == np.inf
#print(df[mask])
#exit()

window = MainWindow.mainWindow()
window.setCallbackFunction("process",processRoutes)
window.setCallbackFunction("Routes",load_timing_points)
window.setCallbackFunction("getTrack",getTrack)
window.setCallbackFunction("getDate",get_date)
window.setCallbackFunction("singleTrack",process_single_track)
window.mainloop()
del df


