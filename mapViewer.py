from math import *
from pyglet.gl import *
import itertools
from itertools import chain
import pickle
import time
from pyglet.window import mouse
pyglet.options['debug_gl'] = False




width = 100
height = 100
mapScale = 1
topLeftOfImage = [0,0]
TAU = 2 * pi
pixelCoords = []
RED = (255, 0, 0)       # for points
GREY = (128,128,128)
WHITE = (255,255,255)

class MapViewer(pyglet.window.Window):
    def __init__(self,width,height):
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
        self.fps_display = pyglet.clock.ClockDisplay()
        self.currentPosition = 0
        self.visiblePoints = []
        self.visibleLines = []
        self.leftMouseDown = False
        self.mapScale = 1
        self.activity = None
        self.pixelToMilesRatio = 0.3343211478136297 / 0.020022057657865237
        self.currentClosenessThreshold = 0.02  ### how close a point needs to get to a timing point to be marked as close
        self.timingPointsToDisplay = 0  ### primary direction
        self.currentlySelectedPoint = -1
        self.notifyTimingPointAddedFunction = None
        self.visibleBatch = pyglet.graphics.Batch()
        self.invisibleBatch = pyglet.graphics.Batch()
        with open("coords.pkl","rb") as f:
            self.pixelCoords =pickle.load(f)#[200:205]
        self.set_up_vertex_lists()
        self.set_background_color(120,120,120,1)
        self.selectedVertexLists = []
        #self.vertexList = self.circle(100, 100, 5, 200, RED + RED * 200, self.visibleBatch,None)

    def set_background_color(self,r, g, b, a):
        self.background = pyglet.image.SolidColorImagePattern((r, g, b, a)).create_image(800, 800)


    def on_mouse_motion(self,x,y,dx,dy):
        #print(x,y,dx,dy)
        pass


    def on_mouse_press(self,x, y, button, modifiers):
        print("mouse down")
        if button==1:
            print("here")
            self.activity = "mapSelected"
            self.dragInfo = {}
            self.dragInfo["tag"] = "map"
            self.dragInfo["coords"] = (x,y)

    def on_mouse_release(self,x,y,button,modifiers):
        print("mouse up")
        if self.activity is None:
            return
        if self.activity == "mapSelected":
            iw, ih = self.width, self.height
            # calculate crop window size
            cw, ch = iw / self.mapScale, ih / self.mapScale

            print("map was moved", x - self.dragInfo["coords"][0], y - self.dragInfo["coords"][1])
            if x - self.dragInfo["coords"][0] != 0 or y - self.dragInfo["coords"][1] != 0:
                print("changin")
                print("topleft was ", self.topLeftOfImage)
                self.topLeftOfImage[0] -= (x - self.dragInfo["coords"][0]
                    ) / self.mapScale  # *(1280 / self.mapScale)/self.width
                self.topLeftOfImage[1] -= (y - self.dragInfo["coords"][1]
                    ) / self.mapScale  # * (1280 / self.mapScale)/self.height
                print("topleft is now ",self.topLeftOfImage)
                self.redraw_canvas()
        self.activity = None

    def on_mouse_drag(self,x, y, dx, dy, buttons, modifiers):
        print("mouse drag",x, y, dx, dy)

    def on_mouse_scroll(self,x,y,scroll_x,scroll_y):
        print("scrolled",x,y,scroll_x,scroll_y)
        iw, ih = self.width,self.height
        previousCw = iw / self.mapScale
        val = scroll_y
        if val > 0:
            self.mapScale *= scroll_y * 2
        else:
            self.mapScale /= -scroll_y * 2

        print("map scale is", self.mapScale)
        #if self.mapScale > 512:
            #self.mapScale = 512
        cw, ch = iw / self.mapScale, ih / self.mapScale
        diff = previousCw - cw
        print("diff is",diff)
        self.topLeftOfImage[0] += diff / 2
        self.topLeftOfImage[1] -= diff / 2
        if self.mapScale <= 1:
            self.mapScale = 1
            self.topLeftOfImage = [0,self.height]
        print("top left of image is now",self.topLeftOfImage)
        start = time.time() * 1000
        self.redraw_canvas()
        print("redraw canvas took",time.time()*1000 - start)

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
        return self.visibleBatch.add_indexed(n + 2, pyglet.gl.GL_TRIANGLES, group, index, ('v2f/dynamic', p), ('c3B/static', (c + c[-3:])))

    def on_draw(self):
        start = time.time() * 1000
        #glEnable(GL_BLEND)
       # glEnable(GL_DEPTH_TEST)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        #glEnable(GL_LINE_SMOOTH)
        #glHint(GL_LINE_SMOOTH_HINT, GL_FASTEST)
        pyglet.gl.glLineWidth(6)
        gl.glClearColor(232/255,232/255,232/255, 1.0)
        self.clear()
        print("no of prpmitives drawn",len(self.smallCirclesList + self.largeCirclesList))
        #glEnable(GL_POINT_SMOOTH)
        #glHint(GL_POINT_SMOOTH_HINT, GL_FASTEST)
        glPointSize(6)
        self.smallCircles.draw_subset(self.smallCirclesList)
        glPointSize(16)
        self.largeCircles.draw_subset(self.largeCirclesList)

        #self.smallCircles.migrate()

        self.visibleBatch.draw_subset(self.visiblePoints)
        self.fps_display.draw()
        #if not self.background is None:
            #self.background.blit(0, 0)
        print("on draw took", time.time() * 1000 - start)

    def set_up_vertex_lists(self):
        radius = 7
        self.pointsAsVertices =[]
        self.linesAsVertices = []
        self.smallCirclesList= []
        self.largeCirclesList= []
        lineGroup = pyglet.graphics.OrderedGroup(1)
        circleGroup = pyglet.graphics.OrderedGroup(0)
        self.smallCircles = pyglet.graphics.Batch()
        self.largeCircles = pyglet.graphics.Batch()
        previousX = 0
        previousY = 0
        visiblePoints = [(i, c) for i, c in enumerate(self.pixelCoords)]
        self.pixelCoords = visiblePoints
        start = time.time() * 1000
        for index, p in enumerate(visiblePoints):
            #print(index,p)
            x, y = p[1]
            y = self.height-y
            result1 = self.smallCircles.add(1,GL_POINTS,circleGroup,("v2f/dynamic",[x,y]),('c3B/static', (245,244,244))) #self.circle(x, y, radius, 10, WHITE + GREY * 10, self.visibleBatch,circleGroup)
            result2 = self.largeCircles.add(1,GL_POINTS,circleGroup,("v2f/dynamic",[x,y]),('c3B/static', (96,96,96))) #self.circle(x, y, radius, 10, WHITE + GREY * 10, self.visibleBatch,circleGroup)
            self.pointsAsVertices.append((result1,result2))
            self.smallCirclesList.append(result1)
            self.largeCirclesList.append(result2)
            if index > 0:
                result = self.visibleBatch.add(2,GL_LINES,lineGroup,("v2f/dynamic",[x,y,previousX,previousY]),('c3B/static', (96,96,96,96,96,96)))
                self.linesAsVertices.append(result)
                self.visibleLines.append(result)
            previousX = x
            previousY = y
        print("no of vertices set up",len(self.pointsAsVertices),len(self.linesAsVertices))
        print("took",time.time() * 1000 - start)

    def redraw_canvas(self):
        iw, ih = self.width,self.height #width,height
        # calculate crop window size
        cw, ch = iw / self.mapScale, ih / self.mapScale
        print("cw", cw, ch)
        print("viewport iwetrwetwetwws", self.topLeftOfImage[0], self.topLeftOfImage[0] + cw, self.topLeftOfImage[1],
              self.topLeftOfImage[1] + ch,"mapscale",self.mapScale)
        if cw > iw or ch > ih:
            cw = iw
            ch = ih
        # crop it
        ###
        ### self.topLeftOfImage is the absolute coords of the displayed part of the map
        ### eg [100,100] would mean that (0,0) on the map panel would be showing [100,100] of the base map image
        ###
        self.visiblePoints = []
        self.visibleLines = []
        self.smallCirclesList = []
        self.largeCirclesList= []
        start = time.time() * 1000
        visiblePoints = [p[0] for p in self.pixelCoords if p[1][0] > self.topLeftOfImage[0] and p[1][0] < self.topLeftOfImage[0] + cw and self.pixelCoords if p[1][1] < self.topLeftOfImage[1] and p[1][1] > self.topLeftOfImage[1] - ch]
        print("setting up visible points took", time.time() * 1000 - start)
        print("no of visible points would be", len(visiblePoints))
        resolution = int(len(visiblePoints)/2000)
        if resolution < 1:
            resolution = 1
        temp = []
        start = time.time() * 1000
        print("res is",resolution)

        ####
        ### calculate the new x and y values for all points
        ###
        for point in self.pixelCoords:
            x, y = point[1]
            x -= self.topLeftOfImage[0]
            y = self.topLeftOfImage[1] - y
            x = (x * self.mapScale)
            y = (y * self.mapScale)
            temp.append((x,y))
        print("calcs took",time.time()*1000-start)
        pointCount = 0
        for count,pointIndex in enumerate(visiblePoints):
            if count % resolution == 0:
                x, y, = temp[pointIndex]
                smallCircleVertices = self.pointsAsVertices[pointIndex][0].vertices
                largeCircleVertices = self.pointsAsVertices[pointIndex][1].vertices
                dx = x - smallCircleVertices[0]
                dy = y - smallCircleVertices[1]
                #print("old x y ", vertices[:2], "new x y ", x, y,"diff",dx,dy,"actual x y",p)
                for i in range(0, len(smallCircleVertices), 2):
                    smallCircleVertices[i] = smallCircleVertices[i] + dx
                    smallCircleVertices[i + 1] = smallCircleVertices[i + 1] + dy
                    largeCircleVertices[i] = largeCircleVertices[i] + dx
                    largeCircleVertices[i + 1] = largeCircleVertices[i + 1] + dy
                self.smallCirclesList.append(self.pointsAsVertices[pointIndex][0])
                self.largeCirclesList.append(self.pointsAsVertices[pointIndex][1])
                pointCount+=1
                if resolution <= 6:
                    if pointIndex>0:
                        vertices = self.linesAsVertices[pointIndex - 1].vertices
                        x1,y1 = temp[pointIndex-1]
                        l = [x, y, x1,y1]
                        for i in range(len(vertices)):
                            vertices[i] = l[i]
                        self.visiblePoints.append(self.linesAsVertices[pointIndex - 1])


            if self.mapScale > 1500:
                midpoint = ((x1 + x) / 2, (y1 + y) / 2)
                dx = x - x1
                dy = y - y1
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
                    p2 = (midpoint[0] - 10 * unit_x, midpoint[1] - 10 * unit_y)
                    p3 = (midpoint[0] + 10 * unit_x, midpoint[1] + 10 * unit_y)
                    #self.create_polygon([p1, p2, p3], fill="indian red")
                    #self.create_line([midpoint, p1], fill="sienna", width=2)

                #self.create_oval([x1 - 8, y1 - 8, x1 + 8, y1 + 8], fill=col, width=0, tags=tags)
                #self.create_oval([x1 - 5, y1 - 5, x1 + 5, y1 + 5], fill="white", width=0, tags=tags)
                #self.circle(x, y, 8, 200, RED + RED * 200, self.batch)
            #self.create_oval([x - 8, y - 8, x + 8, y + 8], fill=col, width=0, tags=tags)
            #self.create_oval([x - 5, y - 5, x + 5, y + 5], fill="white", width=0, tags=tags)
        print("no of points displayed", pointCount)

        ###
        ### draw the currently selected point
        ###

        if self.currentlySelectedPoint != -1:
            x, y = self.pixelCoords[self.currentlySelectedPoint]
            if self.currentlySelectedPoint == 0:
                x1, y1 = self.pixelCoords[self.currentlySelectedPoint]
            else:
                x1, y1 = self.pixelCoords[self.currentlySelectedPoint - 1]
            x -= self.topLeftOfImage[0]
            y -= self.topLeftOfImage[1]
            x = (x * self.mapScale)
            y = (y * self.mapScale)
            x1 -= self.topLeftOfImage[0]
            y1 -= self.topLeftOfImage[1]
            x1 = (x1 * self.mapScale)
            y1 = (y1 * self.mapScale)
            #self.create_line(x, y, x1, y1, fill="gold", width=8, tags=extraTags)
            #self.create_oval([x1 - 5, y1 - 5, x1 + 5, y1 + 5], fill="gold", width=0)
            #self.create_oval([x1 - 3, y1 - 3, x1 + 3, y1 + 3], fill="white", width=0)
            #self.create_oval([x - 8, y - 8, x + 8, y + 8], fill="gold", width=0)
            #self.create_oval([x - 5, y - 5, x + 5, y + 5], fill="white", width=0)

        ###
        ### display the timing points
        ###

        return
        print("timing poitns to display is", self.timingPointsToDisplay)
        if self.timingPointsToDisplay == 0:
            tpList = [(self.timingPoints[0], 0)]
        else:
            tpList = [(self.timingPoints[1], 1)]
        for tps, direction in tpList:
            for p in tps:
                # print("processing",p)
                if p[2][0] >= self.topLeftOfImage[0] - (2 * cw) and p[2][0] <= self.topLeftOfImage[0] + 2 * cw and p[2][
                    1] >= self.topLeftOfImage[1] - (2 * cw) and p[2][1] <= self.topLeftOfImage[1] + 2 * cw:
                    x, y = p[2][0], p[2][1]
                    x -= self.topLeftOfImage[0]
                    y -= self.topLeftOfImage[1]
                    x = (x * self.mapScale)
                    y = (y * self.mapScale)
                    index = p[0]
                    #self.create_line(x, y, x, y - 80, fill="red", width=5,
                                     #tags=[str(direction) + "_timingpoint_" + str(index), ])
                    #self.create_polygon([x, y - 78, x - 30, y - 62, x, y - 40], fill="red",
                                        #tags=[str(direction) + "_timingpoint_" + str(index), ])
                    #self.create_line(x - 2, y, x - 2, y - 80, fill="red4", width=2,
                                     #tags=[str(direction) + "_timingpoint_" + str(index), ])
                    #self.create_line(x + 2, y, x + 2, y - 80, fill="goldenrod", width=2,
                                     #tags=[str(direction) + "_timingpoint_" + str(index), ])
                    #self.create_oval(x - 22, y - 70, x - 2, y - 50, fill="gold",
                                     #tags=[str(direction) + "_timingpoint_" + str(index), ])
                    #self.create_text(x - 12, y - 60, text=str(index), font=("Purisa", 10),
                                     #tags=[str(direction) + "_timingpoint_" + str(index), ])
                    ###
                    ### draw a circle to show what points get picked up by the timing point when the route is processed
                    ###
                    dx = (self.pixelToMilesRatio * self.currentClosenessThreshold) / cw * self.width
                    dy = (self.pixelToMilesRatio * self.currentClosenessThreshold) / ch * self.height
                    #self.create_oval(x - dx, y - dy, x + dx, y + dy, fill="", outline="gold", width=3,
                                     #tags=[str(direction) + "_timingpoint_" + str(index), ])

        print("no of points drawn", pointCount)

    def set_coords(self,coords):
        self.pixelCoords = coords
        self.topLeftOfImage[0] = self.pixelCoords[0][0] - int(self.width/2)
        self.topLeftOfImage[1] = self.pixelCoords[0][1] - int(self.height / 2)


window = MapViewer(1500,1000)
#window.push_handlers(pyglet.window.event.WindowEventLogger())
pyglet.app.run()


