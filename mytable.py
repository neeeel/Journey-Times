
import tkinter


class Table(tkinter.Canvas):
    def __init__(self,headings,cellWidth,cellHeight):
        super(Table, self).__init__()
        self.headings = headings ## a list of headers
        self.cellWidth = cellWidth
        self.cellHeight = cellHeight
        self.cells = []
        self.rowcount = 0
        print("headings are",self.headings)


    def configure_heading_colour(self,colour):
        self.headingColour = colour

    def set_headings(self,headings):
        self.headings = headings

    def add_row(self,values):
        if len(values)!= len(self.headings):
            ## throw exception
            return
        self.rowcount+=1
        for i,v in enumerate(values):
            cell = Cell(self.rowcount,i,str(v))
            self.cells.append(cell)
        print("rowcount is",self.rowcount)

    def draw_table(self):
        self.delete(tkinter.ALL)
        x,y, = 10,10
        width, height = len(self.headings) * self.cellWidth, self.rowcount * self.cellHeight
        width+=10
        height+=10
        print("width,height",width,height)
        for row in range(self.rowcount + 1):
            self.create_line(x,y,width,y)
            y+=self.cellHeight
        x, y, = 10, 10
        width += 10
        height += 10
        for col in range(len(self.headings)):
            self.create_line(x, y, x, height)
            x+= self.cellWidth


class Cell():
    def __init__(self,row,column,text,bg="white",fg="black",font = "TkDefaultFont"):
        self.row= row
        self.column = column
        self.text = text
        self.bg = bg
        self.fg = fg
        self.font = font

win = tkinter.Tk()
table = Table([1,2,3],50,50)
table.grid(row=0,column=0)
table.add_row([1,23,4])
table.draw_table()
win.mainloop()