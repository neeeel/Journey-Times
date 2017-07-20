import tkinter
from PIL import Image,ImageDraw,ImageTk
import mapmanager2



class DragAndZoomCanvas(tkinter.Canvas):

    def __init__(self,master,width,height):
        self.tracsisBlue = "#%02x%02x%02x" % (20, 27, 77)
        self.tracsisGrey = "#%02x%02x%02x" % (99, 102, 106)
        super(DragAndZoomCanvas, self).__init__(master=master,width=width,height=height,relief = tkinter.RAISED,borderwidth=2)
        self.width = width
        self.height= height
        self.baseMapImage = None
        self.topLeftOfImage = [0, 0]
        self.pixelCoords = []
        self.timingPoints = []
        self.currentPosition = 0
        self.bind("<Button-1>", self.map_clicked)
        self.bind("<MouseWheel>", self.on_mousewheel)
        self.mapScale = 1
        self.activity = None
        self.pixelToMilesRatio= 0.3343211478136297/0.020022057657865237
        self.currentClosenessThreshold = 0.02 ### how close a point needs to get to a timing point to be marked as close
        self.timingPointsToDisplay = 0 ### primary direction
        self.currentlySelectedPoint = -1
        self.notifyTimingPointAddedFunction = None

    def view_timing_point(self,index):
        iw, ih = self.width, self.height
        # calculate crop window size
        cw, ch = iw / self.mapScale, ih / self.mapScale
        print("cw", cw, ch)
        try:
            x,y = self.timingPoints[self.timingPointsToDisplay][index][2]
        except KeyError as e:
            print("no such timing popint")
            return
        self.topLeftOfImage[0] = x- cw/2
        self.topLeftOfImage[1] = y - ch/2
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
        self.topLeftOfImage[0] = x- cw/2
        self.topLeftOfImage[1] = y - ch/2
        self.currentlySelectedPoint = index
        if redraw==True:
            self.redraw_canvas()

    def on_mousewheel(self,event):

        iw, ih = self.width,self.height
        previousCw = iw / self.mapScale
        print("scaling value is",event.delta * 1 / 120)
        val = event.delta * 1 / 120
        if val > 0:
            self.mapScale *= event.delta * 2 / 120
        else:
            self.mapScale /= event.delta * 2 / -120
        print("scrolling", self.mapScale)
        if self.mapScale <= 1:
            self.mapScale = 1
            #self.topLeftOfImage = [0,0]
        #if self.mapScale > 512:
            #self.mapScale = 512
        cw, ch = iw / self.mapScale, ih / self.mapScale
        diff = previousCw - cw
        print("diff is",diff)
        self.topLeftOfImage[0] += diff / 2
        self.topLeftOfImage[1] += diff / 2
        self.redraw_canvas()

    def redraw_canvas(self,x=0,y=0,keepCurrentPositionInMiddle= False):
        self.delete(tkinter.ALL)
        iw, ih = self.width,self.height
        # calculate crop window size
        cw, ch = iw / self.mapScale, ih / self.mapScale
        print("cw",cw,ch)
        print("viewport is",self.topLeftOfImage[0],self.topLeftOfImage[0] + cw,self.topLeftOfImage[1],self.topLeftOfImage[1] + ch)
        if cw > iw or ch > ih:
            cw = iw
            ch = ih
        # crop it

        if keepCurrentPositionInMiddle:
            ###
            ### we need to adjust the viewport position so that the currently selected point
            ### is in the middle of the map panel, at 400,400
            ###
            pointX,pointY = self.pixelCoords[self.currentlySelectedPoint]
            print("x,y",pointX,pointY)
            self.topLeftOfImage[0]  = pointX - cw/2
            self.topLeftOfImage[1] = pointY - ch/2



        ###
        ### self.topLeftOfImage is the absolute coords of the displayed part of the map
        ### eg [100,100] would mean that (0,0) on the map panel would be showing [100,100] of the base map image
        ###

        resolution = int(1000/self.mapScale) ### how many points we can see, so we see every xth point
        if resolution <1 :
            resolution = 1
        col = "grey40"
        pointCount=0
        extraTags = []
        print("resolution is",resolution,"no of points is",len(self.pixelCoords),"no of visible points is",int(len(self.pixelCoords)/resolution))
        visiblePoints = [(index,p) for index,p in enumerate(self.pixelCoords) if p[0] >= self.topLeftOfImage[0] - (2*cw) and p[0] <= self.topLeftOfImage[0] + 2*cw and p[1] >= self.topLeftOfImage[1]- (2*cw) and p[1] <= self.topLeftOfImage[1] + 2*cw ]

        if len(visiblePoints) < 10000 or resolution < 1:
            resolution = 1
        else:
            resolution = int(len(visiblePoints) / 1500)
        print("no of visible points is", len(visiblePoints),"resolution is",resolution)
        for index,p in enumerate(visiblePoints):
            if index%resolution == 0: ### we only want to display a few points if the resolution is "high"
                pointCount+=1

                previousPointIndex = p[0] - 1
                if previousPointIndex <0 :
                    previousPointIndex = 0
                #print("index of drawn point is",p,"previously drawn point iS",visiblePoints[previousPointIndex])
                x, y = p[1]
                x -= self.topLeftOfImage[0]
                y -= self.topLeftOfImage[1]
                x = (x * self.mapScale)
                y = (y * self.mapScale)
                tags = ["point_" + str(p[0])] + extraTags
                if previousPointIndex >=0:
                    x1,y1 = self.pixelCoords[previousPointIndex]
                    x1 -= self.topLeftOfImage[0]
                    y1 -= self.topLeftOfImage[1]
                    x1 = (x1 * self.mapScale)
                    y1 = (y1 * self.mapScale)
                    self.create_line(x, y, x1, y1, fill=col, width=8,tags = extraTags)
                    if self.mapScale > 500:
                        midpoint = ((x1+x)/2,(y1+y)/2)
                        dx = x-x1
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
                        p1 = (midpoint[0] + (10*unit_x),midpoint[1]  + (10*unit_y))
                        ###
                        ### calculate slope of perpendicular line
                        ###
                        if dy != 0:
                            slope = -dx/dy
                        else:
                            slope =0
                        c = midpoint[1]-(slope*midpoint[0])
                        ### calculate a point 10 pixels along our perpendicular line from the midpoint
                        if dy == 0: ### line is horizontal
                            p2 = (midpoint[0],midpoint[1] - 10)
                            p3 = (midpoint[0], midpoint[1] + 10)
                        elif dx == 0:
                            p2 = (midpoint[0] - 10, midpoint[1])
                            p3 = (midpoint[0]+ 10, midpoint[1] )
                        else:
                            ### take a random point on the perpendicular line
                            ### calculate unit vector
                            ### work out 2 points
                            ###
                            newX = midpoint[0]-20
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
                            p2 = (midpoint[0] - 10* unit_x,midpoint[1] - 10 * unit_y)
                            p3 = (midpoint[0] + 10 * unit_x, midpoint[1] + 10 * unit_y)
                        self.create_polygon([p1,p2,p3],fill = "indian red")
                        self.create_line([midpoint,p1],fill = "sienna",width = 2)

                    self.create_oval([x1 - 8, y1 - 8, x1 + 8, y1 + 8], fill=col, width=0, tags=tags)
                    self.create_oval([x1 - 5, y1 - 5, x1 + 5, y1 + 5], fill="white", width=0, tags=tags)
                self.create_oval([x - 8, y - 8, x + 8, y + 8], fill=col, width=0, tags=tags)
                self.create_oval([x - 5, y - 5, x + 5, y + 5], fill="white", width=0, tags=tags)

        ###
        ### draw the currently selected point
        ###

        if self.currentlySelectedPoint != -1:
            x,y = self.pixelCoords[self.currentlySelectedPoint]
            if self.currentlySelectedPoint == 0:
                x1, y1 = self.pixelCoords[self.currentlySelectedPoint]
            else:
                x1, y1 = self.pixelCoords[self.currentlySelectedPoint-1]
            x -= self.topLeftOfImage[0]
            y -= self.topLeftOfImage[1]
            x = (x * self.mapScale)
            y = (y * self.mapScale)
            x1 -= self.topLeftOfImage[0]
            y1 -= self.topLeftOfImage[1]
            x1 = (x1 * self.mapScale)
            y1 = (y1 * self.mapScale)
            self.create_line(x, y, x1, y1, fill="gold", width=8, tags=extraTags)
            self.create_oval([x1 - 5, y1 - 5, x1 + 5, y1 + 5], fill="gold", width=0)
            self.create_oval([x1 - 3, y1 - 3, x1 + 3, y1 + 3], fill="white", width=0)
            self.create_oval([x - 8, y - 8, x + 8, y + 8], fill="gold", width=0)
            self.create_oval([x - 5, y - 5, x + 5, y + 5], fill="white", width=0)

        ###
        ### display the timing points
        ###
        print("timing poitns to display is",self.timingPointsToDisplay)
        if self.timingPointsToDisplay == 0:
            tpList = [(self.timingPoints[0],0)]
        else:
            tpList = [(self.timingPoints[1],1)]
        for tps,direction in tpList:
            for p in tps:
                #print("processing",p)
                if p[2][0] >= self.topLeftOfImage[0] - (2*cw) and p[2][0] <= self.topLeftOfImage[0] + 2*cw and p[2][1] >= self.topLeftOfImage[1]- (2*cw) and p[2][1] <= self.topLeftOfImage[1] + 2*cw:
                    x, y = p[2][0],p[2][1]
                    x -= self.topLeftOfImage[0]
                    y -= self.topLeftOfImage[1]
                    x = (x * self.mapScale)
                    y = (y * self.mapScale)
                    index = p[0]
                    self.create_line(x,y,x,y- 80,fill = "red",width=5,tags=[str(direction) + "_timingpoint_" + str(index),])
                    self.create_polygon([x,y-78,x - 30,y-62,x,y-40],fill = "red",tags=[str(direction) + "_timingpoint_" + str(index),])
                    self.create_line(x-2, y, x-2, y - 80, fill="red4", width=2, tags=[str(direction) + "_timingpoint_" + str(index), ])
                    self.create_line(x+2, y, x+2, y - 80, fill="goldenrod", width=2, tags=[str(direction) + "_timingpoint_" + str(index), ])
                    self.create_oval(x -22,y-70,x-2,y - 50,fill="gold",tags=[str(direction) + "_timingpoint_" + str(index),])
                    self.create_text(x-12,y-60,text=str(index),font=("Purisa",10),tags=[str(direction) + "_timingpoint_" + str(index),])
                    ###
                    ### draw a circle to show what points get picked up by the timing point when the route is processed
                    ###
                    dx = (self.pixelToMilesRatio * self.currentClosenessThreshold)/cw * self.width
                    dy = (self.pixelToMilesRatio * self.currentClosenessThreshold)/ch * self.height
                    self.create_oval(x-dx,y-dy,x+dx,y+dy,fill = "",outline="gold",width = 3,tags=[str(direction) + "_timingpoint_" + str(index),])

        print("no of points drawn",pointCount)

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
        y += self.topLeftOfImage[1]

        newCoords = mapmanager2.get_lat_lon_from_x_y(self.centrePoint, x, y, 10)
        print("new coords", newCoords)
        self.indexWindow = tkinter.Toplevel()
        tkinter.Label(self.indexWindow,text="Enter Timing Point Index").grid(row=0,column=0)
        self.indexEntry = tkinter.Entry(self.indexWindow)
        self.indexEntry.grid(row=0,column=1)
        tkinter.Button(self.indexWindow,text = "Save",command=lambda c = newCoords: self.save_timing_point(c)).grid(row=1,column=0,columnspan=2)

    def save_timing_point(self,newCoords):
        index = self.indexEntry.get()
        if index == "":
            return
        try:
            int(index)
        except ValueError as e:
            return
        self.route.add_timing_point(newCoords[0],newCoords[1],self.timingPointsToDisplay,index,reorder=True)
        self.indexWindow.destroy()
        self.set_route(self.route)
        self.notifyTimingPointAddedFunction()

    def map_clicked(self,event):
        x = self.canvasx(event.x)
        y = self.canvasy(event.y)
        winX = event.x - self.canvasx(0)
        winY = event.y - self.canvasy(0)
        print("x,y",x,y,"winx,winy",winX,winY)
        if self.activity == "addTimingPoint":
            self.add_timing_point(x,y)

            #self.activity = None
            return
        self.mapClickedCoords = (winX, winY)
        print("clicked at", winX, winY)
        self.dragInfo = {}
        self.dragInfo["xCoord"] = winX
        self.dragInfo["yCoord"] = winY
        widgets  = self.find_overlapping(x-1, y-1,x+1, y+1)
        if widgets != ():
            print("widgets are",widgets)
            tags = []
            tags = [self.gettags(widget) for widget in widgets if len(self.gettags(widget)) != 0]
            print("list of tags is",tags)
            if len(tags) > 0:
                tag = tags[0][0]
                print("selected tag is",tag)
                if "timingpoint" in tag:
                    self.activity = "TimingPointSelected"
                    widgets = self.find_withtag(tag)
                    self.dragInfo["tag"] = tag
                    print("selected timing point ",tag)
                elif "point" in tag:
                    point = int(tag.replace("point_",""))
                    print("point is now",point)
                    self.currentlySelectedPoint = point

                    print("self.currentphotopos is",self.currentlySelectedPoint)
                    self.notifyPointChangeFunction(self.currentlySelectedPoint)
                    return
        else:
            ### user has clicked map only
            self.activity = "mapSelected"
            self.dragInfo["tag"] = "map"
        self.bind("<B1-Motion>", self.on_movement)
        self.bind("<ButtonRelease-1>", self.on_release_to_move_map)


    def set_centre_point(self,p):
        ###
        ### we need to know the centre point that the lat lons were calculated from, in order to be able
        ### to calculate new lat lons or coords based on the same centre point
        ###
        self.centrePoint = p

    def on_release_to_move_map(self,event):
        iw, ih = self.width, self.height
        # calculate crop window size
        cw, ch = iw / self.mapScale, ih / self.mapScale
        winX = event.x - self.canvasx(0)
        winY = event.y - self.canvasy(0)
        print("map was moved", winX - self.mapClickedCoords[0], winY - self.mapClickedCoords[1])
        if self.activity == "mapSelected":
            if winX - self.mapClickedCoords[0] != 0 or winY - self.mapClickedCoords[1] != 0:
                self.topLeftOfImage[0] -= (winX - self.mapClickedCoords[0])/self.mapScale# *(1280 / self.mapScale)/self.width
                self.topLeftOfImage[1] -= (winY - self.mapClickedCoords[1])/self.mapScale#* (1280 / self.mapScale)/self.height
        if self.activity == "TimingPointSelected":
            ###
            ### do stuff with the timing point
            ###
            xMov = winX - self.mapClickedCoords[0]
            yMov = winY - self.mapClickedCoords[1]
            xMov = xMov/self.width * cw
            yMov = yMov/self.height * ch
            tpIndex = int(self.dragInfo["tag"].split("_")[2]) - 1
            direction = int(self.dragInfo["tag"].split("_")[0])
            coords = self.timingPoints[direction][tpIndex][2]
            #print("previous lat lon is",mapmanager2.get_lat_lon_from_x_y(self.centrePoint,coords[0],coords[1],10,size=800))
            print("new coords will be",coords[0]+xMov,coords[1]+yMov)
            self.timingPoints[direction][tpIndex][2] = (coords[0]+xMov,coords[1]+yMov)
            newlatlon = mapmanager2.get_lat_lon_from_x_y(self.centrePoint,coords[0]+xMov,coords[1]+yMov,10,size=800)
            print("newlatlon is",newlatlon)
            self.route.adjust_timing_point(direction,tpIndex+1,newlatlon)
            #self.route.timingPoints[direction][tpIndex][2] = newlatlon


        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease-1>")
        self.redraw_canvas()
        self.activity = None

    def on_movement(self,event):
        winX = event.x - self.canvasx(0)
        winY = event.y - self.canvasy(0)
        newX = winX - self.dragInfo["xCoord"]
        newY = winY - self.dragInfo["yCoord"]
        if self.activity == "mapSelected":
            for child in self.find_all():
                self.move(child, newX, newY)
        if self.activity == "TimingPointSelected":
            for child in self.find_withtag(self.dragInfo["tag"]):
                self.move(child, newX, newY)
        self.dragInfo["xCoord"] = winX
        self.dragInfo["yCoord"] = winY

    def set_coords(self,coords):
        self.pixelCoords = coords
        self.topLeftOfImage[0] = self.pixelCoords[0][0] - int(self.width/2)
        self.topLeftOfImage[1] = self.pixelCoords[0][1] - int(self.height / 2)

    def set_timing_points(self,tps):
        print("TPs are ",tps)
        self.timingPoints = tps

    def set_timing_points_to_display(self,direction):
        self.timingPointsToDisplay = direction
        self.redraw_canvas()

    def set_cursor(self,type):
        ###
        ### setting the cursor also toggles the ability to add a timing point
        ###
        if type == "cross":
            if self.activity is None:
                self.activity = "addTimingPoint"
        else:
            if self.activity == "addTimingPoint":
                self.activity = None
        self.config(cursor=type)

    def set_route(self,route):
        self.route=route
        tps = self.route.get_timing_points()
        primaryTps = [[tp[0], tp[1], mapmanager2.get_coords(self.centrePoint,(tp[2],tp[3]),10,size=800)] for tp in tps[0]]
        secondaryTps =[[tp[0], tp[1], mapmanager2.get_coords(self.centrePoint,(tp[2],tp[3]),10,size=800)] for tp in tps[1]]
        self.timingPoints = [primaryTps,secondaryTps]

    def set_callback_function(self,title,fun):
        if title == "notify change of point":
            self.notifyPointChangeFunction = fun
        if title == "notify added timing point":
            self.notifyTimingPointAddedFunction = fun

points = [(56.40501,-3.45778),(56.40716,-3.48441),(56.44521,-3.47190)]
#coords = [mapmanager2.get_coords(points[0],p,10) for p in points]
#print("coords are ",coords)
#window = tkinter.Tk()
#canvas = DragAndZoomCanvas(window,800,800)
#canvas.set_coords(coords)

#canvas.grid(row=0,column=0)
#tkinter.Button(window,command=canvas.redraw_canvas).grid(row=1,column=0)
#canvas.redraw_canvas()
#window.mainloop()