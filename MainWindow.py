
import tkinter
import tkinter.ttk as ttk
import tkinter.font as font
import datetime
import mapmanager
import openpyxl
import win32com.client
from PIL import Image,ImageDraw,ImageTk
from tkinter import filedialog
import threading
import queue
import copy



class mainWindow(tkinter.Tk):

    def __init__(self):
        super(mainWindow, self).__init__()
        self.routes = {}
        #self.bind("<<finished>>",self.received)
        self.selectedRoute = None
        self.progress = None
        self.trackData = None
        self.q = queue.Queue()
        self.discardedRuns = []
        self.baseData = [] ### store the returned data, ready to display either normal or discarded runs
        self.normalRuns=[]
        self.colours = ["black","red","gold","sea green","deep sky blue"]
        self.processSingleTrackFunction = None
        self.loadRoutesFunction = None
        self.getDateFunction = None
        self.previousLegIndex = -1 # this keeps track of the leg that is displayed yellow, so we dont have to redraw the whole track each time
        self.primaryTrackList = []
        self.secondaryTrackList = []
        self.trackWindow = None
        self.mapMan = None
        self.mapImage = None
        self.wm_title("Journey Times")
        self.state("zoomed")
        self.primaryTrees = []
        self.secondaryTrees = []
        self.configure(bg="white")

        ###
        ### set up menu bar
        ###
        self.menubar = tkinter.Menu(self)
        menu = tkinter.Menu(self.menubar,tearoff = 0)
        menu.add_command(label = "Load TPs",command = self.displayRoutes)
        menu.add_separator()
        menu.add_command(label="Export",command=self.spawn_excel_window)
        self.menubar.add_cascade(label="File",menu = menu)
        self.config(menu=self.menubar)
        menu = tkinter.Menu(self.menubar,tearoff = 0)
        menu.add_command(label ="Journey Time Settings",command = self.spawn_settings_window)
        #menu.add_separator()
        #menu.add_command(label = "Excel Settings",command = self.spawn_excel_window)
        self.menubar.add_cascade(label = "Settings",menu = menu)
        self.thumbnail = None

        labelFont  = font.Font(family='Helvetica', size=16, weight='bold')

        ttk.Style().configure("Treeview.Heading", background="black")

        topFrame = tkinter.Frame(self,width = 890,height = 1000,bg="white")
        subFrame = tkinter.Frame(topFrame, width=100, height=900, bg="white")
        self.routeListBox = tkinter.Listbox(master = subFrame,height = 10,width=15,relief=tkinter.SUNKEN,borderwidth =5,bg="white")
        self.TPListBox = tkinter.Listbox(master=topFrame, height=15, relief=tkinter.SUNKEN, borderwidth=5,bg="white")
        buttonFrame = tkinter.Frame(subFrame,height = 100,bg="white")

        tkinter.Button(buttonFrame,text="+",font = labelFont,bg="white",command=lambda :self.change_zoom(1)).grid(row = 0,column = 0,sticky="n",pady = 10)
        tkinter.Button(buttonFrame, text="-", font=labelFont,bg="white",command=lambda :self.change_zoom(-1)).grid(row=1, column=0,sticky="s",pady = 10)
        buttonFrame.grid(row = 1,column=0,pady = 200)
        self.messageFrame = tkinter.Frame(subFrame,width = 100,height = 200, bg="white")
        self.logoCanvas = tkinter.Canvas(topFrame,width = 200,height = 150,bg="white",borderwidth =0, highlightthickness=0, relief='ridge')
        img = Image.open("tracsis Logo.jpg")
        img =img.resize((int(img.width/2),int(img.height/2)),Image.ANTIALIAS)
        #img.show()
        self.logo = ImageTk.PhotoImage(img)
        self.discardedLabel= tkinter.Label(self,text="Discarded Runs \n 0",font=labelFont,bg= "white")
        self.discardedLabel.grid(row=0,column = 4,sticky= "n")
        self.discardedLabel.bind("<Double-Button-1>",self.display_discarded_runs)
        self.logoCanvas.create_image(5, 5, image=self.logo,anchor = tkinter.NW)
        self.thumbnailCanvas = tkinter.Canvas(master = topFrame,width = 805,height = 805,relief=tkinter.SUNKEN,borderwidth =5,bg="white")
        self.routeListBox.bind('<Double-Button-1>', self.runProcess)
        self.routeListBox.bind('<<ListboxSelect>>', self.showTPs)
        tkinter.Label(topFrame,text = "Route",font=labelFont,justify=tkinter.LEFT,bg="white").grid(row=0,column=0, pady= (0,11),sticky="nw")
        self.mapLabel = tkinter.Label(topFrame, text="Map", font=labelFont,justify=tkinter.LEFT,bg="white")
        self.mapLabel.grid(row=0, column=1,pady= 0,sticky="nw")

        subFrame.grid(row=1,column=0, sticky="nw",padx=0)
        self.routeListBox.grid(row=0, column=0, pady=2, padx=0, sticky="nw")
        #self.messageFrame.grid(row=1,column = 0)


        self.thumbnailCanvas.grid(row=1, column=1, pady=0, padx=0, sticky="nw")
        self.logoCanvas.grid(row=2, column=1, pady=10, padx=10, sticky="nw")
        topFrame.grid(row=0, column=0,sticky="nw", pady=0,padx=0)
        topFrame.grid_propagate(False)


        frame = tkinter.Frame(self,bg="white")
        self.tabs = ttk.Notebook(frame)
        self.matrixFrame = tkinter.Frame(self, relief=tkinter.SUNKEN, borderwidth=5, width=800, height=794,bg="white")
        self.matrixFrame2 = tkinter.Frame(self, relief=tkinter.SUNKEN, borderwidth=5, width=800, height=794,bg="white")
        self.matrixFrame.grid_propagate(False)
        self.matrixFrame2.grid_propagate(False)
        self.tabs.add(self.matrixFrame, text="Primary")
        self.tabs.add(self.matrixFrame2, text="Secondary")
        self.journeyLabel = tkinter.Label(frame, text="Journey Time Summary", font=labelFont,justify=tkinter.LEFT,bg="white")
        self.journeyLabel.grid(row=0, column=0,pady= (0,11),sticky="nw")

        self.tabs.grid(row=1,column=0,sticky="nw")
        ttk.Style().configure("Treeview", background="light grey")
        frame.grid(row=0,column = 1, pady=0, padx=0,sticky="nw")
        self.loadSettings()

    def display_discarded_runs(self,event):
        text = self.discardedLabel.cget("text")
        if "Discarded Runs" in text:
            noOfRuns = len(self.baseData[0][0])
            self.discardedLabel.configure(text="Normal Runs\n" + str(noOfRuns))
            prim = copy.deepcopy(self.baseData[0])
            sec = copy.deepcopy(self.baseData[1])
            dataToDisplay = [[prim[2], prim[1]], [sec[2], sec[1]]]
            self.display_data(dataToDisplay)
        else:
            noOfRuns = len(self.baseData[0][2])
            self.discardedLabel.configure(text="Discarded Runs\n" + str(noOfRuns))
            prim = list(self.baseData[0])
            sec = list(self.baseData[1])
            dataToDisplay = [[prim[0], prim[1]], [sec[0], sec[1]]]
            self.display_data(dataToDisplay)

    def startProgress(self,msg):

        self.progressWin = tkinter.Toplevel(self,width = 200,height = 200)
        x = int(self.winfo_screenwidth()/2 - 100)
        y = int(self.winfo_screenheight() / 2 - 100)
        self.progressWin.attributes("-topmost",True)
        tkinter.Label(self.progressWin,text = msg).grid(row=0,column = 0,padx = 20,pady= 20)
        self.progress = ttk.Progressbar(self.progressWin, orient="horizontal", length=200, mode="indeterminate")
        print("width height",str(self.progressWin.winfo_width()) + "x" + str(self.progressWin.winfo_height()))
        print("progressbar is",type(self.progress))
        self.progress.grid(row=1,column = 0,padx = 20,pady= 20)
        self.progress.start(10)
        print(str(self.progressWin.winfo_width()) + "x" + str(self.progressWin.winfo_height()) + "+" + str(x) + "+" + str(y))
        self.progressWin.geometry("+" + str(x) + "+" + str(y))
        self.progressWin.lift()

    def stopProgress(self):
        #print("in self.stop progress")
        print("progressbar is", type(self.progress))
        if self.progress is None:
            pass
        else:
            self.progress.stop()
            self.progress =None
        self.progressWin.destroy()

    def showTPs(self,event):
        ### Get the current selection in the routes List box, and display the TPS for that route in the TPS list box
        ###
        self.TPListBox.delete(0,tkinter.END)
        routeName = self.routeListBox.get(self.routeListBox.curselection())
        if routeName in self.routes:
            self.mapLabel.configure(text="Map - " + routeName)
            self.thumbnail = ImageTk.PhotoImage(self.routes[routeName].get_map())
            #self.routes[routeName].get_map().show()
            #print("img size is",self.thumbnail.width(),self.thumbnail.height())
            self.thumbnailCanvas.create_image(10, 10, image=self.thumbnail, anchor=tkinter.NW)
            for tps in self.routes[routeName].get_timing_points():
                for point in tps:
                    self.TPListBox.insert(tkinter.END,point)

    def key_pressed(self,event):
        if event.widget in self.primaryTrees[:3]:
            item = self.primaryTrees[0].selection()[0]
            index = self.primaryTrees[0].index(item)
            for tree in self.primaryTrees[:3]:
                tree.delete(item)
                self.map_closed()
            del self.primaryTrackList[index]
        if event.widget in self.secondaryTrees[:3]:
            item = self.secondaryTrees[0].selection()[0]
            index = self.secondaryTrees[0].index(item)
            for tree in self.secondaryTrees[:3]:
                tree.delete(item)
                self.map_closed()
            del self.secondaryTrackList[index]
        self.check_tags(self.primaryTrees, self.primaryTrackList)
        self.check_tags(self.secondaryTrees, self.secondaryTrackList)

    def map_closed(self):
        if self.trackWindow is None:
            pass
        else:
            self.trackWindow.destroy()
            self.trackWindow = None

    def settings_closed(self):
        self.saveSettings()
        self.settingsWindow.destroy()
        self.settingsWindow = None
        text = "Red in Durations Table = duration of journey(or leg of journey) is greater than " + str(
            self.entryValues[7].get()) + "% above the overall average"
        text += "\n\nYellow in Speed Table = Overall average speed is greater than " + str(self.entryValues[6].get())
        children = self.winfo_children()
        for child in children:
            print(child)
        for child in children[5].children.values():
            info = child.grid_info()
            if info["row"] == 0 and info["column" ]==0:
                child.configure(text=text)

        self.check_tags(self.primaryTrees,self.primaryTrackList)
        self.check_tags(self.secondaryTrees,self.secondaryTrackList)

    def excel_settings_closed(self):
        self.excelWindow.destroy()

    def export(self):
        file = filedialog.asksaveasfilename()
        #print(file)
        dir = self.entryValues[4].get()
        am = self.entryValues[1].get()
        ip = self.entryValues[2].get()
        pm = self.entryValues[3].get()
        primaryDirection = self.cbox.get()
        if primaryDirection == "North":
            primaryDirection = "Northbound"
            secondaryDirection = "Southbound"
        if primaryDirection == "South":
            primaryDirection = "Southbound"
            secondaryDirection = "Northbound"
        if primaryDirection == "East":
            primaryDirection = "Eastbound"
            secondaryDirection = "Westbound"
        if primaryDirection == "West":
            primaryDirection = "Westbound"
            secondaryDirection = "Eastbound"
        if primaryDirection == "Clockwise":
            secondaryDirection = "Anticlockwise"
        if primaryDirection == "Anticlockwise":
            secondaryDirection = "Clockwise"

        TPs = [(x[2], x[3]) for x in self.selectedRoute.get_timing_points()[0]]
        self.export_to_excel(self.primaryTrees,TPs,self.primaryTrackList,file + " " + primaryDirection)
        track = self.secondaryTrackList[0]
        TPs = [(x[2], x[3]) for x in self.selectedRoute.get_timing_points()[1]]
        self.export_to_excel(self.secondaryTrees, TPs, self.secondaryTrackList,file + " " + secondaryDirection)

    def export_to_excel(self,trees,timingPoints,trackList,filename):
        AMRuns = 0
        IPRuns = 0
        PMRuns = 0
        runsList = []
        IPRunsList = []
        PMRunsList = []
        am1 = self.entryValues[0].get()
        am2 = self.entryValues[1].get()
        ip1 = self.entryValues[2].get()
        ip2 = self.entryValues[3].get()
        pm1 = self.entryValues[4].get()
        pm2 = self.entryValues[5].get()
        if self.selectedRoute is None:
            return
        img = Image.open("tracsis Logo.jpg")
        imgSmall = img.resize((184,65),Image.ANTIALIAS)
        excelImageSmall = openpyxl.drawing.image.Image(imgSmall)
        excelImage = openpyxl.drawing.image.Image(img)
        self.startProgress("Exporting to Excel")
        self.progressWin.update()
        wb = openpyxl.load_workbook("template.xlsm",keep_vba=True)
        sheets = wb.get_sheet_names()
        wb.get_sheet_by_name(sheets[0]).add_image(excelImage,"B3")
        for sht in sheets[1:-1]:
            sheet = wb.get_sheet_by_name(sht)
            sheet.add_image(excelImageSmall,"A1")
        try:
            sheet = wb.get_sheet_by_name('Temp')
        except Exception as e:
            print(e)
            return
        tpCount = len(self.selectedRoute.get_timing_points()[0])
        #print("no of timing points",len(self.selectedRoute.get_timing_points()[0]))
        for i,child in enumerate(trees[0].get_children()):
            self.progress.step()
            self.progressWin.update()
            flag = False
            #print(self.journeyTimesTree.item(child)["values"])
            #print(trees[0].item(child)["values"][1],type(trees[0].item(child)["values"][1]))
            if datetime.datetime.strptime(trees[0].item(child)["values"][1],"%H:%M:%S").time() >= datetime.datetime.strptime(am1,"%H:%M").time() and \
               datetime.datetime.strptime(trees[0].item(child)["values"][1],"%H:%M:%S").time() <= datetime.datetime.strptime(am2,"%H:%M").time():
                #print(trees[0].item(child)["values"][1],"is an AM Run")
                AMRuns+=1
                flag = True
                #print("adding",child,"to am runs")
                runsList.append(child)
            if datetime.datetime.strptime(trees[0].item(child)["values"][1],"%H:%M:%S").time() >= datetime.datetime.strptime(ip1, "%H:%M").time() and \
               datetime.datetime.strptime(trees[0].item(child)["values"][1],"%H:%M:%S").time() <= datetime.datetime.strptime(ip2, "%H:%M").time():
                #print(trees[0].item(child)["values"][1], "is an IP Run")
                IPRuns += 1
                runsList.append(child)
                #print("adding", child, "to ip runs")
                flag = True
            if datetime.datetime.strptime(trees[0].item(child)["values"][1],"%H:%M:%S").time() >= datetime.datetime.strptime(pm1, "%H:%M").time() and \
               datetime.datetime.strptime(trees[0].item(child)["values"][1],"%H:%M:%S").time() <= datetime.datetime.strptime(pm2,"%H:%M").time():
                #print(trees[0].item(child)["values"][1], "is an PM Run")
                PMRuns += 1
                runsList.append(child)
                #print("adding", child, "to pm runs")
                flag = True
        rawData = []
        print("runslist is",runsList)
        for i,child in enumerate(runsList):
            self.progress.step()
            self.progressWin.update()
            for j in range(tpCount):
                sheet.cell(row=2+i,column = 1 + j).value = trees[0].item(child)["values"][j + 1]
            sheet.cell(row = 2+i,column = 1 + tpCount).value = self.getDateFunction(trackList[i][0])
        #for i,child in enumerate(trees[1].get_children()):
            for j in range(tpCount):
                sheet.cell(row=2 + i, column=j + tpCount + 2).value = trees[1].item(child)["values"][j + 1]
        #for i,child in enumerate(trees[2].get_children()):
            for j in range(tpCount):
                sheet.cell(row=2 + i, column=j + (2 * tpCount) + 2).value = trees[2].item(child)["values"][j + 1]

            ###
            ### dump raw data to the excel sheet
            ###
            data = self.getTrack(trackList[int(child) -1])
            data["Track No"] = "Track " + str(child)
            data[["Track No","Record", "Time", "Lat", "Lon", "legTime", "legSpeed"]].apply(lambda x: rawData.append(x.tolist()), axis=1)

        sheet["A1"] = AMRuns
        sheet["B1"] = self.entryValues[0].get()
        sheet["C1"] = self.entryValues[1].get()
        sheet["D1"] = IPRuns
        sheet["E1"] = self.entryValues[2].get()
        sheet["F1"] = self.entryValues[3].get()
        sheet["G1"] = PMRuns
        sheet["H1"] = self.entryValues[4].get()
        sheet["I1"] = self.entryValues[5].get()
        sheet["J1"] = tpCount
        #primaryTPs = [(x[2], x[3]) for x in self.selectedRoute.get_timing_points()[0]]
        if self.getTrack != None:
            self.mapMan = mapmanager.MapManager(640, 640, 12, timingPoints[0], timingPoints)
            self.trackData = self.getTrack(trackList[0])
        offset=trackList[0][0]
        for i,t in enumerate(trackList[0][:-1]):
            self.progress.step()
            self.progressWin.update()
            #print(track[0][i],track[0][i+1],"offset is",offset)
            #print("dist between tps is",self.trackData["legDist"][self.trackList[0][i]-offset:self.trackList[0][i+1]-offset].sum())
            sheet.cell(row=1,column = 11+i).value = self.trackData["legDist"][trackList[0][i]-offset:trackList[0][i+1]-offset].sum()
        lats = self.trackData["Lat"].tolist()
        lons = self.trackData["Lon"].tolist()
        pathData = list(zip(lats, lons))
        #print("Track data is ",pathData)
        image = self.mapMan.get_map_with_path(timingPoints,pathData)
        excelImage = openpyxl.drawing.image.Image(image)
        sheet = wb.get_sheet_by_name('Location - Distance')
        sheet.add_image(excelImage,"B13")

        sheet = wb.get_sheet_by_name('Raw Data')
        for i,row in enumerate(rawData):
            #print("row",row)
            self.progress.step()
            self.progressWin.update()
            for j,item in enumerate(row):
                sheet.cell(row=i+1,column=j+1).value = item

        wb.save(filename +".xlsm")
        xl = win32com.client.Dispatch("Excel.Application")
        xl.Workbooks.Open(Filename=filename + ".xlsm", ReadOnly=1)
        xl.Application.Run("formatfile")
        xl.Workbooks(1).Close(SaveChanges=1)
        xl.Application.Quit()
        xl = 0
        self.excel_settings_closed()
        self.stopProgress()

    def set_end_point(self,event):
        curItem = event.widget.identify_row(event.y)
       # print("currently viewing track", self.displayedTrackIndex)
        #print("clicked on index",event.widget.index(curItem))
        #print("clicked on ", curItem)
        if self.displayedTrackDirection == "primary":
            currentTrack = self.primaryTrackList[self.displayedTrackIndex]
            TPs = [(x[2], x[3]) for x in self.selectedRoute.get_timing_points()[0]]
            trees = self.primaryTrees
            trackList = self.primaryTrackList
        if self.displayedTrackDirection == "secondary":
            currentTrack = self.secondaryTrackList[self.displayedTrackIndex]
            TPs = [(x[2], x[3]) for x in self.selectedRoute.get_timing_points()[1]]
            trees = self.secondaryTrees
            trackList = self.secondaryTrackList

        index = event.widget.index(curItem) + currentTrack[0]
        if index <currentTrack[-2]:
            return 'break'
        #print("current track data is ", currentTrack, "index is", index)
        currentTrack[-1] = index
        result = self.processSingleTrackFunction(currentTrack[0],currentTrack[-1],TPs)
        #print("received back",result)
        trackList[self.displayedTrackIndex] = result[0]
        trackName = trees[0].item(trees[0].selection()[0], "values")
        # print("row data is",trackName)
        values = result[1]
        values.insert(0, trackName[0])
        trees[0].item(trees[0].selection()[0], values=values)
        values = result[2]
        values.insert(0, trackName[0])
        trees[1].item(trees[1].selection()[0], values=values)
        values = result[3]
        values.insert(0, trackName[0])
        trees[2].item(trees[2].selection()[0], values=values)
        #print(self.primaryTrackList)
        self.check_tags(trees, trackList)
        event.widget.item(curItem, values=result[1])
        self.spawn_track_window(None)
        return 'break'

    def set_start_point(self,event):
        curItem = event.widget.identify_row(event.y)
        #print("currently viewing track", self.displayedTrackIndex)
       # print("clicked on index", event.widget.index(curItem))
        #print("clicked on ", curItem)
        if self.displayedTrackDirection == "primary":
            currentTrack = self.primaryTrackList[self.displayedTrackIndex]
            TPs = [(x[2], x[3]) for x in self.selectedRoute.get_timing_points()[0]]
            trees = self.primaryTrees
            trackList = self.primaryTrackList
        if self.displayedTrackDirection == "secondary":
            currentTrack = self.secondaryTrackList[self.displayedTrackIndex]
            TPs = [(x[2], x[3]) for x in self.selectedRoute.get_timing_points()[1]]
            trees = self.secondaryTrees
            trackList = self.secondaryTrackList

        index = event.widget.index(curItem) + currentTrack[0]
        if index >= currentTrack[1]:
            return 'break'
        #print("current track data is ", currentTrack, "index is", index)
        currentTrack[0] = index
        result = self.processSingleTrackFunction(currentTrack[0], currentTrack[-1], TPs)
        # print("received back",result)
        trackList[self.displayedTrackIndex] = result[0]
        trackName = trees[0].item(trees[0].selection()[0], "values")
        # print("row data is",trackName)
        values = result[1]
        values.insert(0, trackName[0])
        trees[0].item(trees[0].selection()[0], values=values)
        values = result[2]
        values.insert(0, trackName[0])
        trees[1].item(trees[1].selection()[0], values=values)
        values = result[3]
        values.insert(0, trackName[0])
        trees[2].item(trees[2].selection()[0], values=values)
        self.check_tags(trees, trackList)
        event.widget.item(curItem, values=result[1])
        self.spawn_track_window(None)
        return 'break'

    def spawn_track_window(self,event):
        if event is None:
            if self.displayedTrackDirection == "primary":
                index = self.displayedTrackIndex
                track = self.primaryTrackList[self.displayedTrackIndex]
                TPs = [(x[2], x[3]) for x in self.selectedRoute.get_timing_points()[0]]
            if self.displayedTrackDirection == "secondary":
                index = self.displayedTrackIndex
                track = self.secondaryTrackList[self.displayedTrackIndex]
                TPs = [(x[2], x[3]) for x in self.selectedRoute.get_timing_points()[1]]
        else:
            if event.widget in self.primaryTrees:
                #print("selection is",self.primaryTrees[0].selection())
                if self.primaryTrees[0].selection() == "":
                    return
                index =(self.primaryTrees[0].index(self.primaryTrees[0].selection()[0]))
                track = self.primaryTrackList[index]
                self.displayedTrackDirection = "primary"
                self.displayedTrackIndex = index
                TPs = [(x[2], x[3]) for x in self.selectedRoute.get_timing_points()[0]]
            if event.widget in self.secondaryTrees:
                #print("selection is", self.secondaryTrees[0].selection())
                if self.secondaryTrees[0].selection() == "":
                    return
                index = (self.secondaryTrees[0].index(self.secondaryTrees[0].selection()[0]))
                track = self.secondaryTrackList[index]
                self.displayedTrackDirection = "secondary"
                self.displayedTrackIndex = index
                TPs = [(x[2], x[3]) for x in self.selectedRoute.get_timing_points()[1]]
        if self.trackWindow == None:

            #scrollbar = tkinter.Scrollbar(frame).pack(side=tkinter.RIGHT, fill=tkinter.Y)
            self.displayedTrackIndex = index
            self.trackWindow = tkinter.Toplevel(self)
            self.trackWindow.protocol("WM_DELETE_WINDOW", self.map_closed)
            frame = tkinter.Frame(master=self.trackWindow)
            frame.grid(row=0,column=0)
            scroll =tkinter.Scrollbar(frame)
            self.trackTree = ttk.Treeview(frame,columns=(1,2,3,4,5,6),show="headings",height = 7,yscrollcommand=scroll.set)
            scroll.config(command = self.trackTree.yview)
            self.trackTree.grid(row=0,column=0)
            scroll.grid(row=0,column=1,sticky="ns")
            self.trackTree.column(1,width = 65)
            self.trackTree.column(2, width=130)
            self.trackTree.column(3, width=65)
            self.trackTree.column(4, width=65)
            self.trackTree.column(5, width=65)
            self.trackTree.column(6, width=65)
            self.trackTree.heading(1,text="Record")
            self.trackTree.heading(2, text="Time")
            self.trackTree.heading(3, text="Lat")
            self.trackTree.heading(4, text="Lon")
            self.trackTree.heading(5, text="Leg Time")
            self.trackTree.heading(6, text="Leg Speed")

            self.trackTree.bind("<<TreeviewSelect>>",self.draw_track)
            self.trackTree.bind("<Control-1>",self.set_start_point)
            self.trackTree.bind("<Control-Shift-1>", self.set_end_point)


            frame = tkinter.Frame(master=self.trackWindow,width = 800,height  =800)
            frame.grid(row=1,column=0)
            self.mapCanvas = tkinter.Canvas(frame,width = 800,height  =800)
            self.mapCanvas.pack(expand=tkinter.YES, fill=tkinter.BOTH)
        self.trackTree.delete(*self.trackTree.get_children())

        #self.trackTree.tag_configure("speedissue", background="yellow")
        self.mapCanvas.delete("all")
        self.previousLegIndex = -1

        if self.getTrack != None:
            self.mapMan = mapmanager.MapManager(640,640,12,TPs[0],TPs)
            routeName = self.routeListBox.get(self.routeListBox.curselection())
            #for k, v in self.routes.items():
                #print("looking for ", routeName, v.name)
                #if v.name == routeName:
                    #self.mapMan = v.getMapManager()
            self.mapImage =  ImageTk.PhotoImage(self.mapMan.get_map())
            self.mapCanvas.create_image(0, 0, image = self.mapImage, anchor = tkinter.NW)
            self.trackData = self.getTrack(track)
            lats = self.trackData["Lat"].tolist()
            lons = self.trackData["Lon"].tolist()
            pathData = list(zip(lats,lons))
            #self.mapMan.get_map_with_path(primaryTPs,pathData)
            self.trackData[["Record","Time","Lat","Lon","legTime","legSpeed"]].apply(lambda x: self.trackTree.insert("","end",values = x.tolist()),axis  = 1)
            self.trackTree.selection_set(self.trackTree.get_children()[0])
            self.trackTree.focus_set()
            self.trackTree.focus(self.trackTree.get_children()[0])
            self.trackTree.see(self.trackTree.get_children()[0])
            self.draw_track(None)
        self.trackWindow.geometry("800x1000")

    def draw_track(self,event):
        if self.trackData is None:
            return
        if len(self.trackTree.selection()) >0:
            index = (self.trackTree.index(self.trackTree.selection()[0]))
        else:
            index = -1
        if self.previousLegIndex == -1:
            speed = int(self.trackData.iloc[self.previousLegIndex]["legSpeed"])
            #print("speed is",speed,"legindex is",self.previousLegIndex)
            if speed > 75:
                speed  = 75
            self.trackData.apply(lambda row: self.draw_leg((row["Lat"], row["Lon"]), (row["latNext"], row["lonNext"]), row["legSpeed"]), axis=1)
        if index >=0:
            speed = float(self.trackData.iloc[self.previousLegIndex]["legSpeed"])
            #print("speed is",speed)
            #colour = "#%02x%02x%02x" % (self.colour_gradient["r"][speed], self.colour_gradient["g"][speed], self.colour_gradient["b"][speed])

            self.draw_leg(
                (self.trackData.iloc[self.previousLegIndex]["Lat"], self.trackData.iloc[self.previousLegIndex]["Lon"]),
                (self.trackData.iloc[self.previousLegIndex]["latNext"],
                 self.trackData.iloc[self.previousLegIndex]["lonNext"]),speed)
            speed = int(self.trackData.iloc[index]["legSpeed"])
            if speed > 74:
                speed = 74
            #print("speed is", speed)
            #colour = "#%02x%02x%02x" % (
            #self.colour_gradient["r"][speed], self.colour_gradient["g"][speed], self.colour_gradient["b"][speed])
            self.draw_leg((self.trackData.iloc[index]["Lat"],self.trackData.iloc[index]["Lon"]),(self.trackData.iloc[index]["latNext"],self.trackData.iloc[index]["lonNext"]),-1)
            self.previousLegIndex = index

    def draw_leg(self,p1, p2, speed):
        #print("in leg speed, speed is",speed)
        if speed == -1:
            colour = "white"
        else:
            flag = False
            for i in range(0, 8, 2):
                #print(i, speed, self.entryValues[8 + i].get(), self.entryValues[8 + i + 1].get())
                if speed >= float(self.entryValues[8 + i].get()) and speed <= float(self.entryValues[8 + i + 1].get()):
                    colour = self.colours[int(i / 2)]
                    flag = True
                    #print("colour is", colour)
            if speed > float(self.entryValues[16].get()):
                colour = self.colours[-1]
                flag = True
            if not flag:
                colour = "white"
        #print("colour is",colour)
        x, y = self.mapMan.get_coords(p1)
        self.mapCanvas.create_oval([x - 5, y - 5, x + 5, y + 5], fill=colour,width=0)
        #d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=colour)
        x1, y1 = self.mapMan.get_coords(p2)
        self.mapCanvas.create_oval([x1 - 5, y1 - 5, x1 + 5, y1 + 5], fill=colour,width=0)
        #d.ellipse([x1 - 5, y1 - 5, x1 + 5, y1 + 5], fill=colour)

        self.mapCanvas.create_line(x, y, x1, y1, fill=colour, width=6, smooth=True, splinesteps=400)
        #self.mapCanvas.create_oval([x - 1, y - 1, x + 1, y + 1], fill="white",width=0)
        #self.mapCanvas.create_oval([x1 - 1, y1 - 1, x1 + 1, y1 + 1], fill="white",width=0)
        #d.line([x, y, x1, y1], fill=colour, width=6)
        #d.ellipse([x - 3, y - 3, x + 3, y + 3], fill="white")
        #d.ellipse([x1 - 3, y1 - 3, x1 + 3, y1 + 3], fill="white")

    def list_selected(self,event):
        if event.widget in self.primaryTrees[:3]:
            curItem = event.widget.identify_row(event.y)
            for tree in self.primaryTrees[:3]:
                tree.selection_set(curItem)
                tree.focus_set()
                tree.see(curItem)
        if event.widget in self.secondaryTrees[:3]:
            curItem = event.widget.identify_row(event.y)
            for tree in self.secondaryTrees[:3]:
                tree.selection_set(curItem)
                tree.focus_set()
                tree.see(curItem)
        return 'break'

    def receive_processed_data(self,result):
        self.baseData = result
        print("result is",result)
        if result == []:
            return
        prim = copy.deepcopy(self.baseData[0])
        sec = copy.deepcopy(self.baseData[1])
        dataToDisplay = [[prim[0],prim[1]],[sec[0],sec[1]]]
        noOfRuns = len(self.baseData[0][2])
        self.discardedLabel.configure(text="Discarded Runs\n" + str(noOfRuns))
        self.display_data(dataToDisplay)

    def display_data(self, result):

        if result is None:
            #print("Stopping progress now -----")
            self.stopProgress()
            return
        #self.discardedRuns = result[1]
        primary = result[0]
        secondary = result[1]
        # print("Secondary is ",secondary)
        self.displayPrimary(primary)
        self.displaySecondary(secondary)
        #("Stopping progress now")
        self.stopProgress()

    def runProcess(self,event):
        for tree in self.primaryTrees:
            tree.forget()
            tree.destroy()
        for tree in self.secondaryTrees:
            tree.forget()
            tree.destroy()
        routeName = self.routeListBox.get(self.routeListBox.curselection())
        if not routeName in self.routes:
            self.mapLabel.configure(text="Map")
            self.journeyLabel.configure(text="Journey Time Summary")
            return

        file = filedialog.askopenfilename(initialdir=dir)
        if file == "":
            self.mapLabel.configure(text="Map")
            self.journeyLabel.configure(text="Journey Time Summary")
            return
        self.selectedRoute = self.routes[routeName]
        threading.Thread(target=wrapper_function,args = (self.fun,self.routes[routeName],file)).start()
        self.startProgress("Loading and Processing Data")
        self.mapLabel.configure(text="Map - " + routeName)
        self.journeyLabel.configure(text="Journey Time Summary - " + routeName)
        return

    def spawn_excel_window(self):
        self.excelWindow = tkinter.Toplevel(self)
        self.excelWindow.protocol("WM_DELETE_WINDOW", self.excel_settings_closed)
        frame = tkinter.Frame(self.excelWindow)
        #self.entryValues = []
        self.labels = []
        for i in range(6):
            self.labels.append(tkinter.Label(frame,anchor = tkinter.CENTER))
            self.entryValues.append(tkinter.StringVar())
        self.labels[0].config(text="AM Times")
        self.labels[1].config(text="IP Times")
        self.labels[2].config(text="PM Times")
        for i in range(3,6):
            self.labels[i].config(text="to")

        for i in range(3):

            self.labels[i].grid(row=i, column=0, padx=2, pady=2)
            tkinter.Entry(frame, textvariable=self.entryValues[2*i], width=7).grid(row=i, column=1, padx=2, pady=2)
            self.labels[3+i].grid(row=i, column=2, padx=5, pady=5)
            tkinter.Entry(frame, textvariable=self.entryValues[(2*i)+1], width=7).grid(row=i, column=3, padx=2, pady=2)
        tkinter.Label(frame,text = "Primary Direction").grid(row = 3,column = 0)
        self.entryValues.append(tkinter.StringVar())
        self.cbox = ttk.Combobox(frame,values=["North","South", "East","West", "Clockwise","Anticlockwise"],width = 13)
        self.cbox.grid(row = 3 ,column = 1)
        self.cbox.current(0)
        frame.grid(padx=10, pady=10)
        tkinter.Checkbutton(frame,text = "Primary")
        tkinter.Button(frame,text = "Export",command = self.export).grid(row  = 4,column  = 0,padx=10, pady=10)
        tkinter.Button(frame, text="Exit", command = self.excel_settings_closed).grid(row=4, column=1,padx=10, pady=10)

    def spawn_settings_window(self):
        self.settingsWindow = tkinter.Toplevel(self)
        self.settingsWindow.protocol("WM_DELETE_WINDOW", self.settings_closed)
        frame = tkinter.Frame(self.settingsWindow)
        self.labels = []
        for i in range(7):
            self.labels.append(tkinter.Label(frame))
        self.labels[0].config(text = "Warning Speed")
        self.labels[1].config(text="Average Duration Warning %")
        self.labels[2].config(text="Congested/Stopped")
        self.labels[3].config(text="Slow")
        self.labels[4].config(text="Free Flowing - slow")
        self.labels[5].config(text="Free Flowing")
        self.labels[6].config(text="Free Flowing - fast")
        for i in range(2):
            self.labels[i].grid(row = i,column  = 0,padx = 2,pady =2)
            tkinter.Entry(frame,textvariable = self.entryValues[6 +i],width = 5).grid(row = i,column = 1)
        for i in range(2,7):
            self.labels[i].grid(row = i,column = 0)
        for i in range(5):
            #print(i)
            tkinter.Entry(frame, textvariable=self.entryValues[8 + (i * 2)], width=5).grid(row=2 + i, column=1)
            tkinter.Label(frame,text = "to").grid(row = 2 + i,column = 2)
            tkinter.Entry(frame, textvariable=self.entryValues[8 + (i *2) + 1], width=5).grid(row=2 + i, column=3)
        #print(frame.winfo_children()[-1].winfo_name())
        frame.winfo_children()[-1].grid_forget()
        frame.winfo_children()[-2].grid_forget()

        #tkinter.Button(frame, text="Save", command=self.saveSettings).grid(row=2, column=0, padx=10, pady=10)
        tkinter.Button(frame, text="Exit", command=self.settings_closed).grid(row=11, column=1, padx=10, pady=10)
        frame.grid(padx = 10,pady =10)

    def check_tags(self,trees,trackList):

        ###
        ### calculate and display the average durations
        ###
        if trees is None or trees == [] or trackList is None:
            return
        l = []
        for row in trees[1].get_children():
            l.append(trees[1].item(row)[
                         "values"])  # we now have a list of lists, each sublist is the duration times for a specific leg of a journey
        l = list(zip(*l))[
            1:]  # zip the list of lists together , so that durations for the same leg are in the same list, knock off first list as that just contains the track numbers
        #print(l)
        denom = len(l[0])
        l = [[datetime.datetime.strptime(t, "%H:%M:%S") for t in sublist] for sublist in
             l]  # convert the strings to datetimes
        l = ["0" + str(
            sum([datetime.timedelta(seconds=init.hour * 3600 + init.minute * 60 + init.second) for init in sublist],
                datetime.timedelta(0)) / denom).split(".")[0] for sublist in
             l]  # convert the datetimes to timedeltas, sum the timedeltas, get the average, convert to string, format the string removing decimal places etc
        l.insert(0, "")
        #print(l)
        trees[3].delete(trees[3].get_children())
        trees[3].insert("", "end", values=l)

        ###
        ### calculate and display the average speeds
        ###

        l = []
        for row in trees[2].get_children():
            l.append(trees[2].item(row)["values"])
        l = list(zip(*l))[
            1:]  # zip the list of lists together , so that speeds for the same leg are in the same list, knock off first list as that just contains the track numbers
        l = [[float(t) for t in sublist] for sublist in l]  # convert the strings to floats
        l = [round(sum(item) / len(item), 2) for item in l]
        #print(l)

        l.insert(0, "")
        trees[4].delete(trees[4].get_children())
        trees[4].insert("", "end", values=l)


        ###
        ### check the durations to see if any are over average by X%
        ###
        if trees == []:
            return
        l = [x for x in trees[3].item(trees[3].get_children()[0])["values"]]
        #print("l is",l)
        for child in trees[1].get_children():
            durationtags = []
            for i, cell in enumerate(trees[1].item(child)["values"][1:]):
                averageTime = datetime.datetime.strptime(l[i + 1], "%H:%M:%S")
                t = datetime.datetime.strptime(cell, "%H:%M:%S")
                diff = (t - averageTime).total_seconds()
                denom = averageTime.minute * 60 + averageTime.second
                if denom !=0:
                    if diff * 100 / denom > float(self.entryValues[7].get()):
                        durationtags = ["timeissue"]
                trees[1].item(child, tags=durationtags)
        ###
        ### check if any average speed is greater than X
        ###
        speedtags = ["speedissue"]
        for child in trees[2].get_children():
            for i, cell in enumerate(trees[2].item(child)["values"][1:]):
                #print("checking",cell,float(self.entryValues[6].get()),float(cell) >= float(self.entryValues[6].get()))
                if float(cell) >= float(self.entryValues[6].get()):
                    #print("setting tag")
                    trees[2].item(child,tags=speedtags)
                    break
                else:
                    #print("clearing tag")
                    trees[2].item(child, tags=[])


        ###
        ### check the journey times to see if any are have same end time
        ###
        l = []

        for child in trees[0].get_children():
            trees[0].item(child,tags = [])
            #print("child is ", child)
            #print(trees[0].item(child)["values"])
            l.append((child,trees[0].item(child)["values"][-1]))
        #print("list of finish times is ", l)
        l2 = [x[1] for x in l]
        l = [child for child, x in l if l2.count(x) > 1]
        #print("l is ", l)
        [trees[0].item(i , tags=("timeissue",)) for i in l]

    def displaySecondary(self, result):
        for tree in self.secondaryTrees:
            tree.forget()
            tree.destroy()
        if result is None:
            return
        #print("result in secondary is",result)
        if result[0] == []:
            return
        distances = result[1]
        result = result[0] # because result contains both track and distance data
        if len(result) > 0:

            #####
            #####   Set up the new tables
            #####

            for tree in self.secondaryTrees:
                tree.forget()
                tree.destroy()
            self.secondaryTrees = []
            labels = []
            width = 65
            cols = tuple(range(len(result[0][0]) + 1))
            totalWidth = len(cols) * width
            self.secondaryTrees.append(
                ttk.Treeview(master=self.matrixFrame2, columns=cols, show="headings", height=8))  ### journeytimes tree
            self.secondaryTrees.append(
                ttk.Treeview(master=self.matrixFrame2, columns=cols, show="headings", height=8))  ### durations tree
            self.secondaryTrees.append(
                ttk.Treeview(master=self.matrixFrame2, columns=cols, show="headings", height=8))  ### speed tree

            for tree in self.secondaryTrees:  ### set up the first column in all the trees
                tree.column(0, width=width, anchor='center')
                tree.heading(0, text='Track')
                tree.bind("<BackSpace>", self.key_pressed)
                tree.bind("<Delete>", self.key_pressed)
                tree.bind("<Double-Button-1>", self.spawn_track_window)
                tree.bind("<Button-1>", self.list_selected)

            for tree in self.secondaryTrees:
                for i in range(1, len(result[0][0]) + 1):  ### set up column headings for journey times
                    tree.column(i, width=width, anchor='center')
            self.secondaryTrees[1].heading(cols[-1], text="Total")
            self.secondaryTrees[2].heading(cols[-1], text="Average")

            self.secondaryTrees.append(ttk.Treeview(master=self.matrixFrame2, columns=cols, height=1,
                                              show="headings"))  ### average durations tree
            self.secondaryTrees[3].column(0, width=width, anchor='center')
            self.secondaryTrees[3].column(cols[-1], width=width, anchor="center")
            self.secondaryTrees.append(
            ttk.Treeview(master=self.matrixFrame2, columns=cols, height=1, show="headings"))  #### average speed tree
            self.secondaryTrees[4].column(0, width=width, anchor='center')
            self.secondaryTrees[4].column(cols[-1], width=width, anchor="center")
            self.secondaryTrees.append(
                ttk.Treeview(master=self.matrixFrame2, columns=cols, height=1,show="headings"))  #### distance tree
            self.secondaryTrees[5].column(0, width=width, anchor='center')
            self.secondaryTrees[5].column(cols[-1], width=width, anchor="center")

            for i in range(1, len(result[0][0]) + 1):
                self.secondaryTrees[4].column(i, width=width, anchor='center')
                self.secondaryTrees[0].column(i, width=width, anchor='center')
                self.secondaryTrees[0].heading(i, text='TP' + str(i))

            for i in range(1, len(result[0][0]) + 1):  ### set up column headings for journey times
                self.secondaryTrees[4].column(i, width=width, anchor='center')
                self.secondaryTrees[0].column(i, width=width, anchor='center')
                self.secondaryTrees[0].heading(i, text='TP' + str(i))

            for tree in self.secondaryTrees[1:3]:  ### set up column headings and widths for duration and speed tables
                for i in range(1, len(result[0][0])):
                    tree.column(i, width=width, anchor='center')
                    tree.heading(i, text='TP' + str(i) + ' - TP' + str(i + 1))

            for tree in self.secondaryTrees[3:6]:  ### set up column widths for average tables
                for i in range(1, len(result[0][0])):
                    tree.column(i, width=width, anchor='center')
                    tree.heading(i, text='TP' + str(i) + ' - TP' + str(i + 1))

            self.secondaryTrees[3].heading(0, text="Average")
            self.secondaryTrees[4].heading(0, text="Average")
            self.secondaryTrees[5].heading(0, text="Distance")
            self.secondaryTrees[3].heading(len(result[0][0]), text="Total")
            self.secondaryTrees[4].heading(len(result[0][0]), text="Total")
            self.secondaryTrees[5].heading(len(result[0][0]), text="Total")

            ####
            #### set up the tags to denote different colours of rows
            ####

            self.secondaryTrees[0].tag_configure("timeissue", background="green")
            self.secondaryTrees[1].tag_configure("timeissue", background="red")
            self.secondaryTrees[2].tag_configure("speedissue", background="yellow")

            ###
            ### grid up the trees
            self.secondaryTrees[0].grid(row=0, column=0, pady=10, padx=10)
            self.secondaryTrees[1].grid(row=1, column=0, pady=(10,0), padx=10)
            self.secondaryTrees[2].grid(row=3, column=0, pady=(10,0), padx=10)
            self.secondaryTrees[3].grid(row=2, column=0, pady=(0,10), padx=10)
            self.secondaryTrees[4].grid(row=4, column=0, pady=(0,10), padx=10)
            self.secondaryTrees[5].grid(row=5, column=0, pady=10, padx=10)

            ttk.Style().configure("Treeview", background="light grey")

            self.secondaryTrackList = [x[0] for x in
                              result]  ## self.tracklist is a list of lists, each entry is a list of indexes into the dataframe, indicating when that track hit a timing point

            ####
            ####      Go through the results, add them to the various tables
            ####
            for i, r in enumerate(result):


                ### insert the journey times

                times, speeds = r[1], r[2]
                times.insert(0, "Track " + str(i + 1))
                self.secondaryTrees[0].insert("", "end", iid=i+1, values=times)

                ### insert the Durations

                times = times[1:]
                l = []
                for j in range(len(times) - 1):
                    l.append(datetime.datetime.strptime(times[j + 1], "%H:%M:%S") - datetime.datetime.strptime(times[j],
                                                                                                               "%H:%M:%S"))
                s = sum(l, datetime.timedelta())
                l.insert(0, "Track " + str(i + 1))
                l.insert(cols[-1], s)  ### insert
                self.secondaryTrees[1].insert("", "end", iid=i+1, values=l)

                ### insert the speeds

                speeds.insert(0, "Track " + str(i + 1))
                self.secondaryTrees[2].insert("", "end", iid=i+1, values=speeds)
            if totalWidth < 500:
                totalWidth = 500
            #self.geometry(str(totalWidth + 60) + "x900")

            ###
            ### calculate and display the average durations
            ###

            l = []
            for row in self.secondaryTrees[1].get_children():
                l.append(self.secondaryTrees[1].item(row)[
                             "values"])  # we now have a list of lists, each sublist is the duration times for a specific leg of a journey
            l = list(zip(*l))[
                1:]  # zip the list of lists together , so that durations for the same leg are in the same list, knock off first list as that just contains the track numbers
            #print(l)
            denom = len(l[0])
            l = [[datetime.datetime.strptime(t, "%H:%M:%S") for t in sublist] for sublist in l]  # convert the strings to datetimes
            l = ["0" + str(
                sum([datetime.timedelta(seconds=init.hour * 3600 + init.minute * 60 + init.second) for init in sublist],
                    datetime.timedelta(0)) / denom).split(".")[0] for sublist in
                 l]  # convert the datetimes to timedeltas, sum the timedeltas, get the average, convert to string, format the string removing decimal places etc
            l.insert(0, "")
            #print(l)
            self.secondaryTrees[3].insert("", "end", values=l)


            ###
            ### calculate and display the average speeds
            ###

            l = []
            for row in self.secondaryTrees[2].get_children():
                l.append(self.secondaryTrees[2].item(row)["values"])
            l = list(zip(*l))[
                1:]  # zip the list of lists together , so that speeds for the same leg are in the same list, knock off first list as that just contains the track numbers
            l = [[float(t) for t in sublist] for sublist in l]  # convert the strings to floats
            #print(l)
            l = [round(sum(item) / len(item), 2) for item in l]
            #print(l)
            l.insert(0, "")
            self.secondaryTrees[4].insert("", "end", values=l)
            self.check_tags(self.secondaryTrees,self.secondaryTrackList)

        ###
        ### display the distance data
        ###

        distances.insert(0,"")
        self.secondaryTrees[5].insert("","end",values=distances)

    def displayPrimary(self,result):
        for tree in self.primaryTrees:
            tree.forget()
            tree.destroy()
        if result is None:
            return
        #print("result in primary is", result)
        #print("result is",result)
        if result[0] ==[]:
            return

        distances = result[1]
        result = result[0]
        print("result is",result)
        if len(result) > 0:

            #####
            #####   Set up the new tables
            #####


            self.primaryTrees = []
            labels = []
            width = 65
            cols = tuple(range(len(result[0][0]) + 1))
            totalWidth = len(cols) * width
            self.primaryTrees.append(
                ttk.Treeview(master=self.matrixFrame, columns=cols, show="headings", height=8))  ### journeytimes tree
            self.primaryTrees.append(
                ttk.Treeview(master=self.matrixFrame, columns=cols, show="headings", height=8))  ### durations tree
            self.primaryTrees.append(
                ttk.Treeview(master=self.matrixFrame, columns=cols, show="headings", height=8))  ### speed tree

            for tree in self.primaryTrees:  ### set up the first column in all the trees
                tree.column(0, width=width, anchor='center')
                tree.heading(0, text='Track')
                tree.bind("<BackSpace>", self.key_pressed)
                tree.bind("<Delete>", self.key_pressed)
                tree.bind("<Double-Button-1>", self.spawn_track_window)
                tree.bind("<Button-1>", self.list_selected)

            for tree in self.primaryTrees:  ### set up the end columns for the 2nd two tables
                tree.column(cols[-1], width=width, anchor="center")
            self.primaryTrees[1].heading(cols[-1], text="Total")
            self.primaryTrees[2].heading(cols[-1], text="Average")

            self.primaryTrees.append(ttk.Treeview(master=self.matrixFrame, columns=cols, height=1,
                                                  show="headings"))  ### average durations tree
            self.primaryTrees[3].column(0, width=width, anchor='center')
            self.primaryTrees[3].column(cols[-1], width=width, anchor="center")
            self.primaryTrees.append(
                ttk.Treeview(master=self.matrixFrame, columns=cols, height=1, show="headings"))  #### average speed tree
            self.primaryTrees[4].column(0, width=width, anchor='center')
            self.primaryTrees[4].column(cols[-1], width=width, anchor="center")
            self.primaryTrees.append(
                ttk.Treeview(master=self.matrixFrame, columns=cols, height=1, show="headings"))  #### distance tree
            self.primaryTrees[5].column(0, width=width, anchor='center')
            self.primaryTrees[5].column(cols[-1], width=width, anchor="center")

            for i in range(1, len(result[0][0]) + 1):  ### set up column headings for journey times
                self.primaryTrees[4].column(i, width=width, anchor='center')
                self.primaryTrees[0].column(i, width=width, anchor='center')
                self.primaryTrees[0].heading(i, text='TP' + str(i))

            for tree in self.primaryTrees[1:3]:  ### set up column headings and widths for duration and speed tables
                for i in range(1, len(result[0][0])):
                    tree.column(i, width=width, anchor='center')
                    tree.heading(i, text='TP' + str(i) + ' - TP' + str(i + 1))

            for tree in self.primaryTrees[3:6]:  ### set up column headings and widths for duration and speed tables
                for i in range(1, len(result[0][0])):
                    tree.heading(i, text='TP' + str(i) + ' - TP' + str(i + 1))
                    tree.column(i, width=width, anchor='center')
            self.primaryTrees[3].heading(0,text="Average")
            self.primaryTrees[4].heading(0, text="Average")
            self.primaryTrees[5].heading(0, text="Distance")
            self.primaryTrees[3].heading(len(result[0][0]), text="Total")
            self.primaryTrees[4].heading(len(result[0][0]), text="Total")
            self.primaryTrees[5].heading(len(result[0][0]), text="Total")

            ####
            #### set up the tags to denote different colours of rows
            ####

            self.primaryTrees[0].tag_configure("timeissue",background = "green")
            self.primaryTrees[1].tag_configure("timeissue", background="red")
            self.primaryTrees[2].tag_configure("speedissue", background="yellow")

            ###
            ### grid up the trees
            self.primaryTrees[0].grid(row=0, column=0, pady=10, padx=10)
            self.primaryTrees[1].grid(row=1, column=0, pady=(10,0), padx=10)
            self.primaryTrees[2].grid(row=3, column=0, pady=(10,0), padx=10)
            self.primaryTrees[3].grid(row=2, column=0, pady=(0,10), padx=10)
            self.primaryTrees[4].grid(row=4, column=0, pady=(0,10), padx=10)
            self.primaryTrees[5].grid(row=5, column=0, pady=10, padx=10)

            ttk.Style().configure("Treeview", background="light grey")

            self.primaryTrackList = [x[0] for x in
                              result]  ## self.tracklist is a list of lists, each entry is a list of indexes into the dataframe, indicating when that track hit a timing point

            ####
            ####      Go through the results, add them to the various tables
            ####
            for i, r in enumerate(result):


                times, speeds = r[1], r[2]
                times.insert(0, "Track " + str(i + 1))
                self.primaryTrees[0].insert("", "end", iid=i+1, values=times)

                ### insert the Durations

                times = times[1:]
                l = []
                for j in range(len(times) - 1):
                    l.append(datetime.datetime.strptime(times[j + 1], "%H:%M:%S") - datetime.datetime.strptime(times[j],
                                                                                                               "%H:%M:%S"))
                s = sum(l, datetime.timedelta())
                l.insert(0, "Track " + str(i + 1))
                l.insert(cols[-1], s)  ### insert
                self.primaryTrees[1].insert("", "end", iid=i+1, values=l)

                ### insert the speeds

                speeds.insert(0, "Track " + str(i + 1))
                self.primaryTrees[2].insert("", "end", iid=i+1, values=speeds)

            if totalWidth < 500:
                totalWidth = 500
            #self.geometry(str(totalWidth + 60) + "x900")

            ###
            ### calculate and display the average durations
            ###

            l = []
            for row in self.primaryTrees[1].get_children():
                l.append(self.primaryTrees[1].item(row)[
                             "values"])  # we now have a list of lists, each sublist is the duration times for a specific leg of a journey
            l = list(zip(*l))[
                1:]  # zip the list of lists together , so that durations for the same leg are in the same list, knock off first list as that just contains the track numbers
            #print(l)
            denom = len(l[0])
            l = [[datetime.datetime.strptime(t, "%H:%M:%S") for t in sublist] for sublist in
                 l]  # convert the strings to datetimes
            l = ["0" + str(
                sum([datetime.timedelta(seconds=init.hour * 3600 + init.minute * 60 + init.second) for init in sublist],
                    datetime.timedelta(0)) / denom).split(".")[0] for sublist in
                 l]  # convert the datetimes to timedeltas, sum the timedeltas, get the average, convert to string, format the string removing decimal places etc
            l.insert(0, "")
            #print(l)
            self.primaryTrees[3].insert("", "end", values=l)


            ###
            ### calculate and display the average speeds
            ###

            l = []
            for row in self.primaryTrees[2].get_children():
                l.append(self.primaryTrees[2].item(row)["values"])
            l = list(zip(*l))[
                1:]  # zip the list of lists together , so that speeds for the same leg are in the same list, knock off first list as that just contains the track numbers
            l = [[float(t) for t in sublist] for sublist in l]  # convert the strings to floats
            #print(l)
            l = [round(sum(item) / len(item), 2) for item in l]
            #print(l)
            l.insert(0, "")
            self.primaryTrees[4].insert("", "end", values=l)
            self.check_tags(self.primaryTrees,self.primaryTrackList)

        ###
        ### display the distance data
        ###

        distances.insert(0, "")
        self.primaryTrees[5].insert("", "end", values=distances)

    def OnMouseWheel(self, event):
        self.journeyTimesTree.yview("scroll", -event.delta, "units")
        self.durationsTree.yview("scroll", -event.delta, "units")
        # this prevents default bindings from firing, which
        # would end up scrolling the widget twice
        return "break"

    def pressed(self):
        self.tree.forget()
        self.tree = ttk.Treeview(master=self.matrixFrame, columns=["1","2","3"], show="headings")
        self.tree.grid(row=0, column=0)
        self.tree.columns = ["1","2","3"]
        self.tree.heading("1",text = "Phoo")
        self.tree.insert("","end",values = ("wew","terte","fan"))
        self.tree.insert("","end",values=("wew", "terte", "fan"))

    def setCallbackFunction(self,text,fun):
        if text == "Routes":
            self.loadRoutesFunction = fun
        if text =="process":
            self.fun = fun
        if text == "getTrack":
            self.getTrack = fun
        if text == "getDate":
            self.getDateFunction = fun
        if text == "singleTrack":
            self.processSingleTrackFunction = fun

    def change_zoom(self,val):
        routeName = self.routeListBox.get(self.routeListBox.curselection())

        for k, v in self.routes.items():
            print("looking for ", routeName,v.name)
            if v.name == routeName:

                v.update_zoom(val)
                self.thumbnail = ImageTk.PhotoImage(v.get_map())
                self.thumbnailCanvas.create_image(10, 10, image=self.thumbnail, anchor=tkinter.NW)

    def displayRoutes(self):

        #threading.Thread(target = self.fun,args=(1,2)).start()
        #self.startProgress("Loading Timing Points")
       # print("hurrah")
        #return

        #self.event_generate("<<finished>>")
        for tree in self.primaryTrees:
            tree.forget()
            tree.destroy()
        for tree in self.secondaryTrees:
            tree.forget()
            tree.destroy()
        self.routeListBox.delete(0,tkinter.END)
        self.routes = self.loadRoutesFunction()
        if self.routes is None:
            return
        #self.startProgress("Loading Timing Points")
        for k,v in self.routes.items():
            #print(v.name)
            tps = [(x[2],x[3]) for x in v.get_timing_points()[0]]
            mp = mapmanager.MapManager(640, 640, 11, tps[0], tps)
            v.add_map(mp.get_thumbnail())
            v.setMapManager(mp)
            self.routeListBox.insert(tkinter.END,v.name)
        #self.stopProgress()

    def loadSettings(self):
        self.entryValues = []
        for i in range(18):
            self.entryValues.append(tkinter.StringVar())
        with open('settings.txt', 'r') as f:
            count = 0
            for e in self.entryValues:
                text = f.readline()
                text = text.replace("\n", "")
                if text == "":
                    pass
                e.set(text)
                print("loading",text)

    def saveSettings(self):
        with open('settings.txt', 'w') as f:
            for e in self.entryValues:
                print("writing ", e.get())
                if e.get() == "":
                    f.write("\n")
                else:
                    f.write(str(e.get()) + "\n")

def wrapper_function(fun,routeName,file):
    result = fun(routeName,file)
    #self.q.put(result)
    return

def test_fun():
    for  i in range(10000000):
        print(i)
    return


def hex_to_RGB(hex):
    ''' "#FFFFFF" -> [255,255,255] '''
    # Pass 16 to the integer function for change of base
    return [int(hex[i:i + 2], 16) for i in range(1, 6, 2)]

def RGB_to_hex(RGB):
    ''' [255,255,255] -> "#FFFFFF" '''
    # Components need to be integers for hex to make sense
    RGB = [int(x) for x in RGB]
    return "#" + "".join(["0{0:x}".format(v) if v < 16 else
                          "{0:x}".format(v) for v in RGB])

def color_dict(gradient):
  ''' Takes in a list of RGB sub-lists and returns dictionary of
    colors in RGB and hex form for use in a graphing function
    defined later on '''
  return {"hex":[RGB_to_hex(RGB) for RGB in gradient],
      "r":[RGB[0] for RGB in gradient],
      "g":[RGB[1] for RGB in gradient],
      "b":[RGB[2] for RGB in gradient]}

def linear_gradient(start_hex, finish_hex="#FFFFFF", n=10):
  ''' returns a gradient list of (n) colors between
    two hex colors. start_hex and finish_hex
    should be the full six-digit color string,
    inlcuding the number sign ("#FFFFFF") '''
  # Starting and ending colors in RGB form
  s = hex_to_RGB(start_hex)
  f = hex_to_RGB(finish_hex)
  #print(s,f)
  # Initilize a list of the output colors with the starting color
  RGB_list = [s]
  # Calcuate a color at each evenly spaced value of t from 1 to n
  for t in range(1, n):
    # Interpolate RGB vector for color at the current value of t
    curr_vector = [
      int(s[j] + (float(t)/(n-1))*(f[j]-s[j]))
      for j in range(3)
    ]
    # Add it to our list of output colors
    RGB_list.append(curr_vector)

  return color_dict(RGB_list)

#window = mainWindow()
#window.spawn_track_window(None)
#window.mainloop()
