from math import *
from pyglet.gl import *
import itertools
from itertools import chain
import pickle
import time
from pyglet.window import mouse
pyglet.options['debug_gl'] = False
from scipy.spatial.distance import cdist
import numpy as np
import utilities as ut
from PIL import Image
import mapmanager2
import threading
import tkinter




width = 100
height = 100
mapScale = 1
topLeftOfImage = [0,0]
TAU = 2 * pi
pixelCoords = []
RED = (255, 0, 0)       # for points
GREY = (128,128,128)
WHITE = (255,255,255)
TRACSIS_BLUE = (20, 27, 77)
TRANSLUCENT_YELLOW = (255,255,0,100)
class MapViewer(pyglet.window.Window):
    def __init__(self,width,height,left):
        super(MapViewer, self).__init__(width,height)

        self.label = pyglet.text.Label('Hello, world',
                                  font_name='Times New Roman',
                                  font_size=36,
                                  x=width // 2, y=height // 2,
                                  anchor_x='center', anchor_y='center')
        self.tracsisBlue = "#%02x%02x%02x" % (20, 27, 77)
        self.tracsisGrey = "#%02x%02x%02x" % (99, 102, 106)
        self.background = None
        self.width = width
        self.height = height
        self.baseMapImage = None
        self.topLeftOfImage =[0, self.height]
        self.pixelCoords = []
        self.timingPoints = []
        self.currentPosition = 0
        self.previousPosition = 0
        self.dragging = False
        self.mapScale = 1
        self.activity = None
        self.runIndices = None
        self.isAlive = True
        self.pixelToMilesRatio = 0.3343211478136297 / 0.020022057657865237
        self.currentClosenessThreshold = 0.02  ### how close a point needs to get to a timing point to be marked as close
        self.currentDirection = 0  ### primary direction
        self.currentlySelectedPoint = -1
        self.notifyTimingPointAddedFunction = None
        self.largeCircleBatch = pyglet.graphics.Batch()
        self.smallCircleBatch = pyglet.graphics.Batch()
        self.linesBatch = pyglet.graphics.Batch()
        self.currentPointBatch = pyglet.graphics.Batch()
        self.currentPoint_LineBatch = pyglet.graphics.Batch()
        self.triangleBatch = pyglet.graphics.Batch()
        self.GetTickCount = pyglet.clock.tick()
        self.currentDirection = 0
        self.timingPoints = []
        self.set_location(left,30)

    def on_close(self):
        self.isAlive = False
        self.windowClosedFunction()
        self.close()

    def closest_node(self,node):
        temp = []
        start = time.time() * 1000
        # print("res is",resolution)

        ####
        ### calculate the new x and y values for all points
        ###
        if self.runIndices is None:
            return
        print("run indices are",self.runIndices)
        for i,tp in enumerate(self.timingPoints[self.currentDirection]):
            x, y = tp
            x -= self.topLeftOfImage[0]
            y = self.topLeftOfImage[1] - y
            x = (x * self.mapScale)
            y = (y * self.mapScale)
            if node[0] > x - 42 and node[0] < x and node[1] > y +32 and node[1] < y + 64:
                return ("tp",i)

        for point in self.pixelCoords[self.runIndices[0]:self.runIndices[1]]:
            x, y = point
            x -= self.topLeftOfImage[0]
            y = self.topLeftOfImage[1] - y
            x = (x * self.mapScale)
            y = (y * self.mapScale)
            temp.append((x, y))
        print("lenght of temp is",len(temp))

        #temp = np.asarray(temp)
        result = cdist([node], temp)
        print("smallest distance is",np.amin(result))
        print("closestnode took", time.time() * 1000 - start)
        if np.amin(result) <=20:
            if self.runIndices is None:
                point = result.argmin()
            else:
                point = result.argmin() + self.runIndices[0]
            print("returning",point)
            return ("point",point)

        print("treturning -1")
        return [-1]

    def add_timing_point(self,x,y):
        iw, ih = self.width, self.height
        # calculate crop window size
        cw, ch = iw / self.mapScale, ih / self.mapScale
        print("cw", cw, ch)
        print("viewport is", self.topLeftOfImage[0], self.topLeftOfImage[0] + cw, self.topLeftOfImage[1],
              self.topLeftOfImage[1] + ch)
        if cw > iw or ch > ih:
            cw = iw
            ch = ih
            # crop it
        x = (x / self.mapScale)
        y = (y / self.mapScale)
        x += self.topLeftOfImage[0]
        y = self.topLeftOfImage[1] - y
        newCoords = mapmanager2.get_lat_lon_from_x_y(self.centrePoint, x, y, 10)
        print("new coords", newCoords)
        self.notifyTimingPointAddedFunction([newCoords,self.currentDirection])

    def set_cursor(self,type):
        ###
        ### setting the cursor also toggles the ability to add a timing point
        ###
        print("in set cursor, activity is",self.activity)
        if type == "CURSOR_CROSSHAIR":
            if self.activity is None:
                self.activity = "addTimingPoint"
                cursor = self.get_system_mouse_cursor(self.CURSOR_CROSSHAIR)
                print("setting cursor to crosshair")
        else:
            if self.activity == "addTimingPoint":
                self.activity = None
                cursor = self.get_system_mouse_cursor(self.CURSOR_DEFAULT)
                print("setting cursor to default")

        self.set_mouse_cursor(cursor)

    def set_background_color(self,r, g, b, a):
        self.background = pyglet.image.SolidColorImagePattern((r, g, b, a)).create_image(800, 800)

    def on_mouse_motion(self,x,y,dx,dy):
        pass

    def on_mouse_press(self,x, y, button, modifiers):
        print("mouse down")
        if button == 1:
            if self.activity == "addTimingPoint":
                self.add_timing_point(x, y)

                # self.activity = None
                return
            result = self.closest_node((x,y))
            if result[0] == "point":
                self.previousPosition = self.currentPosition
                self.currentPosition = result[1]
                print("current point is", self.currentPosition)
                self.notifyPointChangeFunction(self.currentPosition)
                self.redraw_canvas()
            elif result[0] == "tp":
                print("selected tp",result[1]+1)
                self.activity = "tpSelected"
                self.selectedTP = result[1]
                self.coordsClicked = (x,y)
            else:
                print("here")
                self.activity = "mapSelected"

                self.dragInfo = {}
                self.dragInfo["tag"] = "map"
                self.dragInfo["coords"] = (x,y)

    def on_mouse_release(self,x,y,button,modifiers):
        if self.activity == "tpSelected":
            coords = self.timingPoints[self.currentDirection][self.selectedTP]
            newlatlon = mapmanager2.get_lat_lon_from_x_y(self.centrePoint,coords[0],coords[1],10,size=800)
            self.route.adjust_timing_point(self.currentDirection, self.selectedTP + 1, newlatlon)
        print("mouse up")
        if self.activity != "addTimingPoint":
            self.activity = None

    def on_mouse_drag(self,x, y, dx, dy, buttons, modifiers):
        if self.activity == "mapSelected":
            self.dragging = True
            self.topLeftOfImage[0] -= dx/ self.mapScale
            self.topLeftOfImage[1] +=dy/ self.mapScale
            #print("topleft is now ", self.topLeftOfImage)
            start = time.time() * 1000
            self.redraw_canvas()
            self.dragging = False
            self.on_draw()
        if self.activity == "tpSelected":
            iw, ih = self.width, self.height
            # calculate crop window size
            cw, ch = iw / self.mapScale, ih / self.mapScale
            dx =  x - self.coordsClicked[0]
            dy = self.coordsClicked[1] - y
            dx = dx / self.width * cw
            dy = dy / self.height * ch
            flag = self.TPMarkers[self.selectedTP]
            flag.x = x
            flag.y= y
            coords = self.timingPoints[self.currentDirection][self.selectedTP]
            self.timingPoints[self.currentDirection][self.selectedTP] = (coords[0] +dx,coords[1]+dy)
            self.coordsClicked = (x,y)
            self.redraw_canvas()
            self.on_draw()

    def on_mouse_scroll(self,x,y,scroll_x,scroll_y):
        iw, ih = self.width,self.height
        previousCw = iw / self.mapScale
        val = scroll_y
        if val > 0:
            self.mapScale *= scroll_y * 2
        else:
            self.mapScale /= -scroll_y * 2
        print("map scale is", self.mapScale)
        if self.mapScale >2048:
            self.mapScale = 2048
        cw, ch = iw / self.mapScale, ih / self.mapScale
        diff = previousCw - cw
        self.topLeftOfImage[0] += diff / 2
        self.topLeftOfImage[1] -= diff / 2
        if self.mapScale <= 1:
            self.mapScale = 1
            self.topLeftOfImage = [0,self.height]
        self.redraw_canvas()

    def redraw_canvas(self):
        temp = []
        ####
        ### calculate the new x and y values for all points
        ###
        if self.runIndices is None:
            start,finish = 0,len(self.pixelCoords)
        else:
            start,finish = self.runIndices
        for index,point in enumerate(self.pixelCoords):
            if index>= start and index<=finish:
                x, y = point
                x -= self.topLeftOfImage[0]
                y = self.topLeftOfImage[1] - y
                x = (x * self.mapScale)
                y = (y * self.mapScale)
            else:
                x,y = -100,-100
            temp.append(x)
            temp.append(y)
        self.largeCirclesVertexList.vertices = temp
        self.smallCirclesVertexList.vertices = temp
        self.linesVertexList.vertices = temp[:4] + temp
        ###
        ### set up current position vertices for the current position line
        ###
        if self.currentPosition >= 1:
            x, y = temp[self.currentPosition * 2], temp[self.currentPosition * 2 + 1]
            x1, y1 = temp[(self.currentPosition - 1) * 2], temp[(self.currentPosition - 1) * 2 + 1]
            self.currentPointVertexList.vertices = [x, y, x1, y1]
            self.currentPoint_LineVertexList.vertices = [x, y, x1, y1]
        ###
        ### set up the triangles
        ###
        vertices = [-100] * (len(temp)-2)*3
        if self.mapScale >= 512:
            for index in range(2,len(temp),2):
                x = temp[index]
                y = temp[index+1]
                if x > 0 and x < self.width and y> 0 and y < self.height:
                    prevX = temp[index-2]
                    prevY = temp[index-1]

                    midpoint = ((prevX + x) / 2, (prevY + y) / 2)
                    dx = x - prevX
                    dy = y - prevY
                    ###
                    ### calcluate unit vector of original line (x,y),(x1,y1)
                    ###
                    mag = ((dx ** 2) + (dy ** 2)) ** (1 / 2)
                    if mag != 0:
                        unit_x = dx / mag
                        unit_y = dy / mag
                    else:
                        unit_x = 0
                        unit_y = 0
                    vertices[((index-2)*3)] = midpoint[0] + (10 * unit_x)
                    vertices[((index-2)*3) + 1] = midpoint[1] + (10 * unit_y)
                    ###
                    ### calculate slope of perpendicular line
                    ###
                    if dy != 0:
                        slope = -dx / dy
                    else:
                        slope = 0
                    c = midpoint[1] - (slope * midpoint[0])
                    ### calculate a point 10 pixels along our perpendicular line from the midpoint
                    if dy == 0:  ### line is horizontal
                        p2 = (midpoint[0], midpoint[1] - 10)
                        p3 = (midpoint[0], midpoint[1] + 10)
                    elif dx == 0:
                        p2 = (midpoint[0] - 10, midpoint[1])
                        p3 = (midpoint[0] + 10, midpoint[1])
                    else:
                        ###
                        ### we can use the previously calculated unit vector(a,b) to give us the perpendicular unit vector(-b,a)
                        ###
                        p2 = (midpoint[0] - (10 * -unit_y), midpoint[1] - (10 * unit_x))
                        p3 = (midpoint[0] + (10 * -unit_y), midpoint[1] + (10 * unit_x))
                    vertices[((index-2)*3) + 2] =p2[0]
                    vertices[((index-2)*3) + 3] =p2[1]
                    vertices[((index-2)*3) + 4] =p3[0]
                    vertices[((index-2)*3) + 5] =p3[1]
        self.triangleVertexList.vertices= vertices
        ###
        ### set up the timing point flags
        ###
        for index,flag in enumerate(self.TPMarkers):
            x,y = self.timingPoints[self.currentDirection][index]
            x -= self.topLeftOfImage[0]
            y = self.topLeftOfImage[1] - y
            x = (x * self.mapScale)
            y = (y * self.mapScale)
            flag.x = x - 42
            flag.y = y
            self.TPNumbers[index].x = int(x -42 + 21)
            self.TPNumbers[index].y = int(y + 50)

    def circle(self,x, y, r, n, c, b,group):
        """ Adds a vertex list of circle polygon to batch and returns it. """
        rad = TAU / n  # getting 360 / n in radians
        index = list(chain.from_iterable((0, x - 1, x) for x in range(2, n + 1)))
        index.extend((0, 1, n))  # end of fan
        p = x, y  # adding center of fan
        for i in range(1, n + 1):
            d = rad * i
            p += int(r * cos(d)) + x, int(r * sin(d)) + y
        p += x + r, y  # adding end of fan

        print(p)
        return list(p)
        return self.largeCircleBatch.add_indexed(n + 2, pyglet.gl.GL_TRIANGLES, group, index, ('v2f/dynamic', p), ('c3B/static', (c + c[-3:])))

    def make_circle(self,numPoints,radius,centre_x,centre_y):
        verts = []
        for i in range(numPoints):
            angle = radians(float(i) / numPoints * 360.0)
            x = (radius * cos(angle)) + centre_x
            y = radius * sin(angle) + centre_y
            verts += [x, y]
        #print(verts)
        return verts

    def draw_test_line(self):
        x, y = 400, 700
        prevX, prevY = 850, 350
        vertices = []
        midpoint = ((prevX + x) / 2, (prevY + y) / 2)
        dx = x - prevX
        dy = y - prevY
        ###
        ### calcluate unit vector of original line (x,y),(x1,y1)
        ###
        mag = ((dx ** 2) + (dy ** 2)) ** (1 / 2)
        if mag != 0:
            unit_x = dx / mag
            unit_y = dy / mag
        else:
            unit_x = 0
            unit_y = 0
        p1 = (midpoint[0] + (10 * unit_x), midpoint[1] + (10 * unit_y))
        vertices.append(midpoint[0] + (10 * unit_x))
        vertices.append(midpoint[1] + (10 * unit_y))
        # print("appending", p1, midpoint[0] + (10 * unit_x), midpoint[1] + (10 * unit_y))
        # print(vertices[:6])
        ###
        ### calculate slope of perpendicular line
        ###
        if dy != 0:
            slope = -dx / dy
        else:
            slope = 0
        c = midpoint[1] - (slope * midpoint[0])
        ### calculate a point 10 pixels along our perpendicular line from the midpoint
        if dy == 0:  ### line is horizontal
            p2 = (midpoint[0], midpoint[1] - 10)
            p3 = (midpoint[0], midpoint[1] + 10)
        elif dx == 0:
            p2 = (midpoint[0] - 10, midpoint[1])
            p3 = (midpoint[0] + 10, midpoint[1])
        else:
            ### take a random point on the perpendicular line
            ### calculate unit vector
            ### work out 2 points
            ###
            newX = midpoint[0] - 20
            newY = (slope * newX) + c
            dx = midpoint[0] - newX
            dy = midpoint[1] - newY
            mag = ((dx ** 2) + (dy ** 2)) ** (1 / 2)
            if mag != 0:
                unit_x = dx / mag
                unit_y = dy / mag
            else:
                unit_x = 0
                unit_y = 0
            p2 = (midpoint[0] - (10 * unit_x), midpoint[1] - (10 * unit_y))
            p3 = (midpoint[0] + (10 * unit_x), midpoint[1] + (10 * unit_y))
        vertices.append(p2[0])
        vertices.append(p2[1])
        vertices.append(p3[0])
        vertices.append(p3[1])

        print("vertices are", vertices)

        pyglet.graphics.draw(2, GL_LINES, ("v2f/stream", (prevX, prevY, x, y)))
        pyglet.graphics.draw(2, GL_LINES, ("v2f/stream", (p2[0], p2[1], p3[0], p3[1])))
        pyglet.graphics.draw(3, GL_TRIANGLES, ("v2f/stream", vertices))
        # self.triangleBatch.draw()
        # return

    def view_timing_point(self,index):
        iw, ih = self.width, self.height
        # calculate crop window size
        cw, ch = iw / self.mapScale, ih / self.mapScale
        print("cw", cw, ch)
        try:
            x,y = self.timingPoints[self.currentDirection][index]
        except KeyError as e:
            print("no such timing popint")
            return
        self.topLeftOfImage[0] = x- cw/2
        self.topLeftOfImage[1] = y + ch/2
        self.redraw_canvas()

    def view_gps_point(self,index,redraw=False):
        iw, ih = self.width, self.height
        # calculate crop window size
        cw, ch = iw / self.mapScale, ih / self.mapScale
        try:
            x,y = self.pixelCoords[index]
        except KeyError as e:
            print("no such timing popint")
            return
        self.topLeftOfImage[0] = x - cw/2
        self.topLeftOfImage[1] = y + ch/2
        self.previousPosition = self.currentPosition
        self.currentPosition = index
        if redraw==True:
            self.redraw_canvas()

    def on_draw(self):
        glEnable(GL_DEPTH_TEST)
        pyglet.gl.glLineWidth(1)
        gl.glClearColor(232 / 255, 232 / 255, 232 / 255, 1.0)
        self.clear()
        ###
        ### draw the circles around the timing points
        ###
        iw, ih = self.width, self.height  # width,height
        # calculate crop window size
        cw, ch = iw / self.mapScale, ih / self.mapScale
        radius = (self.pixelToMilesRatio * self.currentClosenessThreshold) / cw * self.width
        for index,flag in enumerate(self.TPMarkers):
            x,y = flag.x +42,flag.y
            l = self.make_circle(30, radius, x, y)
            pyglet.graphics.draw(30,GL_LINE_LOOP,('v2f', l), ("c4B", TRANSLUCENT_YELLOW * 30))
        pyglet.gl.glLineWidth(6)
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glPointSize(6)
        self.smallCircleBatch.draw()
        glPointSize(16)
        self.largeCircleBatch.draw()
        if self.mapScale >= 512:
            self.triangleBatch.draw()
        self.linesBatch.draw()
        glDisable(GL_DEPTH_TEST)
        self.currentPointBatch.draw()
        self.currentPoint_LineBatch.draw()
        self.TPBatch.draw()
        self.TPNumbersBatch.draw()
        self.flip()

    def set_up_vertex_lists(self):
        self.pointsAsVertices = None
        lineGroup = pyglet.graphics.Group() #OrderedGroup(3)
        largecircleGroup = pyglet.graphics.Group() #.OrderedGroup(2)
        smallCircleGroup= pyglet.graphics.Group() #.OrderedGroup(1)
        self.pointsAsVertices = [element for tupl in self.pixelCoords for element in tupl]
        self.pointsAsVertices = [self.height - item   if index % 2 == 1 else item for index,item in enumerate(self.pointsAsVertices)]
        self.largeCirclesVertexList = self.largeCircleBatch.add(len(self.pointsAsVertices)//2,GL_POINTS,pyglet.graphics.OrderedGroup(5,largecircleGroup),("v2f/stream",self.pointsAsVertices),('c3B/static', GREY * (len(self.pointsAsVertices)//2)))
        self.smallCirclesVertexList = self.smallCircleBatch.add(len(self.pointsAsVertices)//2,GL_POINTS,pyglet.graphics.OrderedGroup(2,smallCircleGroup),("v2f/stream",list(self.pointsAsVertices)),('c3B/static', WHITE * (len(self.pointsAsVertices)//2)))
        self.linesVertexList = self.linesBatch.add(len(self.pointsAsVertices)//2 + 2,GL_LINE_STRIP,pyglet.graphics.OrderedGroup(0,lineGroup),("v2f/stream",self.pointsAsVertices[:2] + list(self.pointsAsVertices) + self.pointsAsVertices[-2:]),('c3B/static', GREY * ((len(self.pointsAsVertices)//2)+2)))
        self.currentPointVertexList = self.currentPointBatch.add(2,GL_POINTS,None,("v2f/stream",self.pointsAsVertices[:4]),('c3B/static', (255,255,0) * 2))
        self.currentPoint_LineVertexList = self.currentPoint_LineBatch.add(2,GL_LINES,None,("v2f/stream",self.pointsAsVertices[:4]),('c3B/static', (255,255,0)*2 ))
        self.currentPosition = 1
        self.previousPosition = 0
        coords = [element for tupl in self.pixelCoords for element in tupl]
        vertices = []
        for index in range(2,len(coords),2):
            x = coords[index]
            y = coords[index + 1]
            prevX = coords[index-2]
            prevY = coords[index-1]
            midpoint = ((prevX + x) / 2, (prevY + y) / 2)
            dx = x - prevX
            dy = y - prevY
            ###
            ### calcluate unit vector of original line (x,y),(x1,y1)
            ###
            mag = ((dx ** 2) + (dy ** 2)) ** (1 / 2)
            if mag != 0:
                unit_x = dx / mag
                unit_y = dy / mag
            else:
                unit_x = 0
                unit_y = 0
            vertices.append(midpoint[0] + (10 * unit_x))
            vertices.append(midpoint[1] + (10 * unit_y))

            ###
            ### calculate slope of perpendicular line
            ###
            if dy != 0:
                slope = -dx / dy
            else:
                slope = 0
            c = midpoint[1] - (slope * midpoint[0])
            ### calculate a point 10 pixels along our perpendicular line from the midpoint
            if dy == 0:  ### line is horizontal
                p2 = (midpoint[0], midpoint[1] - 10)
                p3 = (midpoint[0], midpoint[1] + 10)
            elif dx == 0:
                p2 = (midpoint[0] - 10, midpoint[1])
                p3 = (midpoint[0] + 10, midpoint[1])
            else:
                ### take a random point on the perpendicular line
                ### calculate unit vector
                ### work out 2 points
                ###
                newX = midpoint[0] - 20
                newY = (slope * newX) + c
                dx = midpoint[0] - newX
                dy = midpoint[1] - newY
                mag = ((dx ** 2) + (dy ** 2)) ** (1 / 2)
                if mag != 0:
                    unit_x = dx / mag
                    unit_y = dy / mag
                else:
                    unit_x = 0
                    unit_y = 0
                p2 = (midpoint[0] - (10 * unit_x), midpoint[1] - (10 * unit_y))
                p3 = (midpoint[0] + (10 * unit_x), midpoint[1] + (10 * unit_y))
            vertices.append(p2[0])
            vertices.append(p2[1])
            vertices.append(p3[0])
            vertices.append(p3[1])
        self.triangleVertexList = self.triangleBatch.add(len(vertices)//2,GL_TRIANGLES,None,("v2f/stream",vertices),('c3B/static', RED * (len(vertices)//2)))

    def set_coords(self,coords):
        self.pixelCoords = coords
        self.runIndices = [0,len(self.pixelCoords)]
        self.topLeftOfImage[0] = self.pixelCoords[0][0] - int(self.width/2)
        self.topLeftOfImage[1] = self.pixelCoords[0][1] - int(self.height / 2)
        self.set_up_vertex_lists()
        #self.set_background_color(120, 120, 120, 1)
        print("FINISHED SET UP")
        #pyglet.app.run()

    def set_route(self,route):
        self.route=route
        tps = self.route.get_timing_points()
        primaryTps = [mapmanager2.get_coords(self.centrePoint,(tp[2],tp[3]),10,size=800) for tp in tps[0]]
        secondaryTps =[mapmanager2.get_coords(self.centrePoint,(tp[2],tp[3]),10,size=800) for tp in tps[1]]
        self.timingPoints = [primaryTps,secondaryTps]
        self.currentDirection = 0

        self.set_timing_points_to_display(self.currentDirection)

    def set_timing_points_to_display(self,direction):
        self.currentDirection = direction
        self.TPBatch = pyglet.graphics.Batch()
        self.TPNumbersBatch = pyglet.graphics.Batch()
        self.TPMarkers = []
        self.TPNumbers = []
        flagImage = pyglet.image.load("blue marker.png")
        for index,c in enumerate(self.timingPoints[self.currentDirection]):
            print("adding flag with coords",c)
            flag = pyglet.sprite.Sprite(flagImage, x=c[0], y=c[1], batch=self.TPBatch)
            label = pyglet.text.Label(text=str(index+1),font_size=9,color = (255,255,255,255),batch=self.TPNumbersBatch,x=c[0],y=c[1],anchor_x="left",anchor_y="top",bold=True,italic=True,group=None)
            flag.scale = 0.25
            self.TPMarkers.append(flag)
            self.TPNumbers.append(label)
        self.redraw_canvas()

    def set_centre_point(self,p):
        ###
        ### we need to know the centre point that the lat lons were calculated from, in order to be able
        ### to calculate new lat lons or coords based on the same centre point
        ###
        self.centrePoint = p

    def set_run_indices(self,runIndices):
        self.runIndices = runIndices
        self.redraw_canvas()

    def update(self):
        dt = pyglet.clock.tick()
        self.GetTickCount += dt
        if self.isAlive:
            self.on_draw()
            self.dispatch_events()

    def set_callback_function(self,title,fun):
        if title == "notify change of point":
            self.notifyPointChangeFunction = fun
        if title == "notify added timing point":
            self.notifyTimingPointAddedFunction = fun
        if title == "notify window closed":
            self.windowClosedFunction = fun



