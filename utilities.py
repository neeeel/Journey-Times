### Utility functions for converting grid refs to different formats
import math

def latTOdddd(lat):
    #print(type(lat))
    #init =lat
    lat = float(str(lat)[:2]) + float(str(lat)[2:])/60
    #print("in",init,"out",str(round(lat,5)))
    return round(lat,5)
    #return float("{0:.5f}".format(lat))

def lonTOdddd(lon):
    lon = float(str(lon)[1:2]) + float(str(lon)[2:])/60
    return round(lon*-1,5)
    #return float("{0:.5f}".format(lon*-1))

def latToDecimal(coords):
    lat,long = coords
    lat = lat.replace("N","")
    long = long.replace("W","-")
    return (lat,long)

def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '%.12f' % f
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))

def getDistInMiles(p1,p2):
    #print("processibng",p1,p2)
    if p1 == p2:
        return 0
    lat1,long1 = p1
    lat2,long2 = p2
    return (math.acos((math.cos(math.radians(90 - lat1)) * math.cos(math.radians(90-lat2))) + ((math.sin(math.radians(90 - lat1)) * math.sin(math.radians(90-lat2))) * math.cos(math.radians(long1-long2))))*6371000) * 0.000621371

def getDist(p1,p2):
    x,y = p1
    x1, y1 = p2
    #x=truncate(x,5)
    #y=truncate(y,5)
    x = float(x)
    y = float(y)
    print(p1,x,y)
    #x1 = truncate(x1, 5)
    #y1 = truncate(y1, 5)
    xdiff = abs(x1-x)
    ydiff  = abs(y1-y)
    return math.sqrt(xdiff**2 + ydiff**2)

def get_bearing(p1,p2):
    lat1,lon1 = p1
    lat2,lon2 = p2
    bearing = 360 - (math.degrees(math.atan2(math.sin(lon2 - lon1) * math.cos(lat2),
                         math.cos(lat1) *math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1))) + 360) % 360
    return bearing


points = [(56.40324, -4.64206),(56.381749999999997, -4.6372099999999996)]
points1 = [(56.40324, -4.64206),(56.386969999999998, -4.62052)]
56.386969999999998, -4.62052
print(getDist(points[0],points[1]))
print(getDistInMiles(points[0],points[1]))
print(getDist(points1[0],points1[1]))
print(getDistInMiles(points1[0],points1[1]))
