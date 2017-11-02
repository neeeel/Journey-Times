import tkinter
import tkinter.ttk as ttk
import tkinter.font as font
import datetime
import mapmanager
import openpyxl
import win32com.client
from PIL import Image,ImageDraw,ImageTk,ImageFont
from tkinter import filedialog
from tkinter import messagebox
import threading
import queue
import copy
import time
import os
import dragandzoomcanvas
import mapmanager2
import pandas as pd
import mapViewer
import pickle





class mainWindow(tkinter.Tk):

    def __init__(self):
        super(mainWindow, self).__init__()
        self.routes = {}
        self.tracsisBlue = "#%02x%02x%02x" % (20, 27, 77)
        ttk.Style().configure(".",foreground = self.tracsisBlue,background = "white",weight="bold")
        #self.bind("<<finished>>",self.received)
        self.selectedRoute = None
        self.progress = None
        self.trackData = None
        self.mapViewer = None
        self.unitsVar = tkinter.IntVar()
        self.q = queue.Queue()
        self.discardedRuns = []
        self.baseData = [] ### store the returned data, ready to display either normal or discarded runs
        self.normalRuns=[]
        self.colours = ["black","red","gold","sea green","deep sky blue"]
        self.processSingleTrackFunction = None
        self.loadRoutesFunction = None
        self.getDateFunction = None
        self.getSpeedFunction = None
        self.getfullDataframeFunction = None
        self.previousLegIndex = -1 # this keeps track of the leg that is displayed yellow, so we dont have to redraw the whole track each time
        self.primaryTrackList = []
        self.secondaryTrackList = []
        self.trackWindow = None
        self.mapMan = None
        self.mapImage = None
        self.addTimingPointFlag = False
        self.wm_title("JoPro - Journey Time Software")
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
        menu.add_command(label="Export",command=self.spawn_export_window)
        menu.add_separator()
        menu.add_command(label="View Full Track", command=self.view_full_track)
        self.menubar.add_cascade(label="File",menu = menu)
        self.config(menu=self.menubar)
        menu = tkinter.Menu(self.menubar,tearoff = 0)
        menu.add_command(label ="Journey Time Settings",command = self.spawn_settings_window)
        #menu.add_separator()
        #menu.add_command(label = "Excel Settings",command = self.spawn_excel_window)
        self.menubar.add_cascade(label = "Settings",menu = menu)
        self.thumbnail = None


        leftFrame = tkinter.Frame(self, width=100, height=900, bg="white",relief=tkinter.GROOVE,borderwidth=2)
        labelFont = font.Font(family='Helvetica', size=16, weight='bold')
        tkinter.Label(leftFrame,text = "Route",font=labelFont,bg=self.tracsisBlue,fg="white",relief=tkinter.GROOVE,borderwidth=2).grid(row=0,column=0,sticky="nsew")
        self.routeListBox = tkinter.Listbox(leftFrame,height = 10,width=17,relief=tkinter.GROOVE,borderwidth=2,bg="white")
        self.routeListBox.grid(row=1,column=0,pady=(20,0))
        self.routeListBox.bind('<Double-Button-1>', self.runProcess)
        self.routeListBox.bind('<<ListboxSelect>>', self.showTPs)


        leftFrame.grid(row=0,column=0,sticky="n")
        mapFrame = tkinter.Frame(self,width=800,height=800,relief=tkinter.GROOVE,borderwidth=2)
        mapFrame.grid(row=0,column=1)
        tkinter.Label(mapFrame,text="Map",font=labelFont,bg=self.tracsisBlue,fg="white",relief=tkinter.GROOVE,borderwidth=2).grid(row=0,column=0,sticky="nsew")
        self.thumbnailCanvas = tkinter.Canvas(mapFrame,width = 800,height = 800,relief=tkinter.GROOVE,borderwidth =2,bg="white")
        self.thumbnailCanvas.grid(row=1, column=0,pady=(20,0), sticky="nw")
        tkinter.Label(mapFrame,text="Journey Time Summary",font=labelFont,bg=self.tracsisBlue,fg="white",relief=tkinter.GROOVE,borderwidth=2).grid(row=0,column=1,sticky="nsew")
        self.tabs = ttk.Notebook(mapFrame)
        self.primaryFrame = tkinter.Frame(mapFrame, relief=tkinter.GROOVE,borderwidth=2, width=800, height=800, bg="white")
        self.secondaryFrame = tkinter.Frame(mapFrame, relief=tkinter.GROOVE,borderwidth=2, width=800, height=800, bg="white")
        self.tabs.add(self.primaryFrame, text="Primary")
        self.tabs.add(self.secondaryFrame, text="Secondary")
        self.tabs.bind("<<NotebookTabChanged>>", self.tabChanged)
        self.tabs.grid(row=1, column=1, sticky="nw")
        print(self.tabs.tabs())
        frame = self.nametowidget(self.tabs.tabs()[0])
        print("frame is",type(frame))
        return

    ######################################################################################################
    #
    # Stuff to deal with loading and displaying routes
    #
    ######################################################################################################

    def showTPs(self,event):
        ### Get the current selection in the routes List box, and display the TPS for that route in the TPS list box
        ###
        label = self.winfo_children()[2].winfo_children()[0]
        routeName = self.routeListBox.get(self.routeListBox.curselection())
        if routeName in self.routes:
            label.configure(text="Map - " + routeName)
            self.thumbnail = ImageTk.PhotoImage(self.routes[routeName].get_primary_map())
            self.thumbnailCanvas.create_image(0, 0, image=self.thumbnail, anchor=tkinter.NW)
            self.mapMan = self.routes[routeName].getMapManager()

    def displayRoutes(self):
        for frame in self.tabs.tabs():
            frame = self.nametowidget(frame)
            for child in frame.winfo_children():
                child.destroy()
        self.routeListBox.delete(0,tkinter.END)
        self.routes = self.loadRoutesFunction()
        if self.routes is None:
            return
        for k,v in self.routes.items():
            self.load_route_maps(v)
            self.routeListBox.insert(tkinter.END,v.name)

    def load_route_maps(self,route):
        print("setting up maps for ",route.name)
        prim = [(x[2], x[3]) for x in route.get_timing_points()[0]]
        sec = [(x[2], x[3]) for x in route.get_timing_points()[1]]
        mp = mapmanager.MapManager(640, 640, 11, [], [prim, sec])
        prim, sec = mp.get_thumbnails()
        #prim.show()
        route.add_primary_map(prim)
        route.add_secondary_map(sec)
        route.setMapManager(mp)


    ######################################################################################################
    #
    #
    #
    ######################################################################################################

    def spawn_export_window(self):
        labelFont = font.Font(family='Times', size=12)
        self.excelWindow = tkinter.Toplevel(self)
        self.excelWindow.protocol("WM_DELETE_WINDOW", self.excel_settings_closed)
        frame = tkinter.Frame(self.excelWindow)
        frame.grid(row=0,column=0)
        # routeName = self.routeListBox.get(tkinter.ACTIVE)
        print(";",self.routeListBox.curselection(),":")
        if len(self.routeListBox.curselection()) > 0:
            self.routeListBox.activate(self.routeListBox.curselection())
        self.routeListBox.config(state=tkinter.DISABLED)
        for row,text in enumerate(["AM Times","IP Times","PM Times"]):
            tkinter.Label(frame,text=text,font=labelFont, relief=tkinter.FLAT,borderwidth=1,anchor="e",width = 14).grid(row=row,column=0,sticky="nsew")
            tkinter.Entry(frame,width=7).grid(row=row,column=1)
            tkinter.Label(frame, text="To",font=labelFont, relief=tkinter.FLAT,borderwidth=1,width = 4).grid(row=row, column=2, sticky="nsew")
            tkinter.Entry(frame, width=7).grid(row=row, column=3,padx=(0,20))
        tkinter.Label(frame,text="Primary Dir",font=labelFont, relief=tkinter.FLAT,borderwidth=1,anchor="e",width = 14).grid(row=3,column=0,sticky="nsew")
        ttk.Combobox(frame, values=["North", "South", "East", "West", "Clockwise", "Anticlockwise"],width=13).grid(row=3, column=1,columnspan=3)
        var = tkinter.IntVar()
        var.set(1)
        c = tkinter.Checkbutton(frame, text="Primary",variable =var)
        c.grid(row=4, column=0)
        c.var = var
        var = tkinter.IntVar()
        var.set(1)
        c = tkinter.Checkbutton(frame, text="Secondary",variable =var)
        c.grid(row=4, column=1,columnspan=3)
        c.var = var
        var = tkinter.IntVar()
        c = tkinter.Checkbutton(frame, text="Export Raw Data",variable =var)
        c.grid(row=5, column=1,columnspan=3)
        c.var = var
        var = tkinter.IntVar()
        c = tkinter.Checkbutton(frame, text="Add 1 Hour to Times",variable =var)
        c.grid(row=5, column=0)
        c.var = var
        tkinter.Button(frame, text="Exit", command=self.excel_settings_closed,font=labelFont,width = 8).grid(row=6, column=0)
        tkinter.Button(frame, text="Export", command=lambda:self.export(""),font=labelFont,width = 8).grid(row=6, column=1,columnspan=3)

    def export(self,file):
        file = "beoj"
        if file == "":
            messagebox.showinfo(message="no file name entered, exiting Export")
            self.stopProgress()
            return
        children = self.excelWindow.winfo_children()[0].winfo_children()
        primaryDirection = children[13].get()
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

        for index,val in enumerate([children[14].var.get(),children[15].var.get()]):
            if val == 1:
                folder = os.path.dirname(os.path.abspath(__file__))
                folder = os.path.join(folder, "Runs\\")
                if not os.path.exists(folder):
                    os.makedirs(folder)
                for fileName in os.listdir(folder):
                    file_path = os.path.join(folder, fileName)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(e)
                self.export_to_excel(index)

    def export_to_excel(self,index):
        wb = openpyxl.load_workbook("Template.xlsm", keep_vba=True)
        sheets = wb.get_sheet_names()
        ###
        ### put big logo on front sheet
        ##
        sheet = wb.get_sheet_by_name(sheets[0])
        img = Image.open("tracsis Logo.jpg")
        imgSmall = img.resize((368, 130), Image.ANTIALIAS)
        excelImageSmall = openpyxl.drawing.image.Image(imgSmall)
        sheet.add_image(excelImageSmall, "B3")

        ###
        ### put little logos on the other sheets
        ###
        for sht in sheets[1:-1]:
            sheet = wb.get_sheet_by_name(sht)
            img = Image.open("tracsis Logo.jpg")
            imgSmall = img.resize((184, 65), Image.ANTIALIAS)
            excelImageSmall = openpyxl.drawing.image.Image(imgSmall)
            sheet.add_image(excelImageSmall, "A1")
        try:
            sheet = wb.get_sheet_by_name('Temp')
        except Exception as e:
            print(e)
            return

        timeSettings = []
        for i in [1,3,5,7,9,11]:
            timeSettings.append(self.excelWindow.winfo_children()[0].winfo_children()[i].get())
        print("timesettings are",timeSettings)
        frame = self.nametowidget(self.tabs.tabs()[index])
        tree = frame.winfo_children()[0]
        for child in tree.get_children():
            print("child is",child)
            runIndex = int(child.replace("run_","")) -1
            runData = self.baseData[index][0][runIndex]
            print("run data is",runData)

    def excel_settings_closed(self):
        self.excelWindow.destroy()
        self.routeListBox.config(state=tkinter.NORMAL)

    def view_full_track(self):
        pass

    def spawn_settings_window(self):
        pass

    def tabChanged(self,event):
        pass

    def delete_run_from_tree(self,event):
        item = event.widget.selection()[0]
        parent = event.widget.parent(item)
        if parent != "":
            event.widget.delete(parent)
        else:
            event.widget.delete(item)
        return

    def runProcess(self,event):
        for frame in self.tabs.tabs():
            frame = self.nametowidget(frame)
            for child in frame.winfo_children():
                child.destroy()
        label = self.winfo_children()[2].winfo_children()[0]
        routeName = self.routeListBox.get(tkinter.ACTIVE)
        self.routeListBox.activate(self.routeListBox.curselection())
        if self.routes[routeName].changed:
            ###
            ### reload the route maps if the TPS have been edited
            ###
            self.routes[routeName].changed = False
            self.load_route_maps(self.routes[routeName])
        fileList = list(filedialog.askopenfilenames(initialdir=dir))
        if not routeName in self.routes or fileList == []:
            label.configure(text="Map")
            #self.journeyLabel.configure(text="Journey Time Summary")
            return
        self.selectedRoute = self.routes[routeName]
        threading.Thread(target=self.fun,args = (self.routes[routeName],fileList)).start()
        #self.startProgress("Loading and Processing Data")
        label.configure(text="Map - " + routeName)
        #self.journeyLabel.configure(text="Journey Time Summary - " + routeName)
        return

    def receive_processed_data(self, result):
        ###
        ### result is a list of lists
        ### result[0] holds the primary direction runs
        ### result[1] holds the secondary direction runs
        ### each specific direction holds [data,distances,discarded runs]
        ###
        self.baseData = result
        width = 65
        for index,tab in enumerate(self.tabs.tabs()):
            frame = self.nametowidget(tab)
            if len(result[index]) > 0:
                cols = tuple(range(len(result[0][0]) + 2))
                tree = ttk.Treeview(frame, columns=cols, show="headings", height=38) ### journeytimes tree
                tree.column("#0", width=30)
                tree.tag_configure('duration',foreground = "gray")
                tree.tag_configure('speed',foreground = "gray")
                tree.tag_configure('run', background='light goldenrod yellow', foreground=self.tracsisBlue)
                tree.column(0, width=width, anchor='center')
                tree.heading(0, text='Track')
                #tree.bind("<BackSpace>", self.key_pressed)
                tree.bind("<Delete>", self.delete_run_from_tree)
                #tree.bind("<Double-Button-1>", self.spawn_track_window)
                #tree.bind("<Button-1>", self.list_selected)
                for i in range(1, len(result[0][0])+1):
                    tree.column(i, width=width, anchor='center')
                    tree.heading(i, text='TP' + str(i))
                tree.heading(cols[-1], text="Total")
                tree.column(cols[-1], width=width, anchor='center')
                tree.grid(row=0,column=0)
                for i,row in enumerate(result[index][0]):
                    print("processing row",row[1])
                    durations =[(datetime.datetime.strptime(row[1][i + 1], "%d/%m/%Y %H:%M:%S") -
                                 datetime.datetime.strptime(row[1][i],"%d/%m/%Y %H:%M:%S")) for i in range(len(row[1])-1)]
                    times = [r.split(" ")[1] for r in row[1]]
                    times.append(sum(durations, datetime.timedelta()))
                    durations = ["duration",""] + durations
                    tree.insert("","end",iid="run_" + str(i+1),values=["Track " + str(i+1)] + times,tags=("run",))
                    tree.insert("run_" + str(i+1), "end", iid="duration_" + str(i+1), values=durations,tags=("duration",))
                    tree.insert("run_" + str(i+1), "end", iid="speed_" + str(i+1), values=["speed"] + row[2],tags=("speed",))

    def setCallbackFunction(self,text,fun):
        print("setting callback for ",text,fun)
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
        if text == "getSpeed":
            self.getSpeedFunction = fun
        if text == "getFullTracks":
            self.getFullTracksFunction = fun
        if text == "fullDataframe":
            print("setting fun to ",fun)
            self.getFullDataframeFunction = fun

#win = mainWindow()
#win.mainloop()
