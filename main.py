from tkinter import *
from tkinter.messagebox import askyesno
from tkinter import ttk
from ttkthemes import ThemedTk
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import serial
import serial.tools.list_ports as p
import sqlite3
import datetime

ser = 0
connected = 0

# measurement array
points = np.zeros([3, 9])
distances = np.zeros([8])

# getting default color progression from matplotlib
colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

# separate[0]-> x separate[1]-> y separate[2]-> z,
# this variable is used for parsing coordinates from USB packets
separate = []

# tkinter window init shit
root = ThemedTk()
root.wm_title("Spine Mapper")

# Widgets style
style = ttk.Style(root)
style.theme_use("yaru")

def deleteMeasurement(imieNazwisko, date):  # DELETES WRONG MEASUREMENT
    if askyesno(title='Potwierdzenie', message='Usunąć dane pacenta?'):
        imieNazwiskoSplit = imieNazwisko.split(" ")
        conn = sqlite3.connect('patients.db')
        c = conn.cursor()
        corDate = str(date)
        corDate = corDate.lstrip("('")
        corDate = corDate.rstrip("',)")
        conditions = imieNazwiskoSplit
        conditions.append(corDate)
        print(conditions)
        c.execute("DELETE FROM patients WHERE imie = (?) AND nazwisko = (?) AND czas = (?)", conditions)
        conn.commit()

def deleteRecord(imieNazwisko):
    if askyesno(title='Potwierdzenie', message='Usunąć wszystkie dane pacenta?'):
        imieNazwiskoSplit = imieNazwisko.split(" ")
        conn = sqlite3.connect('patients.db')
        c = conn.cursor()
        c.execute("DELETE FROM patients WHERE imie = (?) AND nazwisko = (?)", imieNazwiskoSplit)
        conn.commit()


def euclid(currentPoints):
    distances = np.zeros([8])
    pointsT = currentPoints.transpose()

    for i in range(8):
        distances[i] = round(np.linalg.norm(pointsT[i] - pointsT[i + 1]), 1)

    return distances

def concatenation():
    concat = ""
    for i in range(9):
        concat += str(points[0, i]) + "," + str(points[1, i]) + "," + str(points[2, i]) + ";"
    return concat

def writeToDB(imie, nazwisko, concat):
    conn = sqlite3.connect('patients.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS patients (
        imie text,
        nazwisko text,
        points text,
        czas text
    )""")

    c.execute("INSERT INTO patients VALUES (?,?,?,?)", (imie, nazwisko, concat, datetime.datetime.today()))

    print("////////////")
    c.execute("SELECT * FROM patients")
    print(c.fetchall())
    print("////////////")

    conn.commit()
    conn.close()


def readFromDB(imieNazwisko):
    imieNazwiskoSplit = imieNazwisko.split(" ")

    conn = sqlite3.connect('patients.db')
    c = conn.cursor()
    print(imieNazwiskoSplit)
    c.execute("SELECT points FROM patients WHERE imie = (?) AND nazwisko = (?)", imieNazwiskoSplit)
    plotsArray = c.fetchall()
    print(plotsArray)
    c.execute("SELECT czas FROM patients WHERE imie = (?) AND nazwisko = (?)", imieNazwiskoSplit)
    czasArray = c.fetchall()
    conn.commit()

    print(len(plotsArray))

    # another tkinter window
    branch = Toplevel()
    branch.wm_title("Spine Comparasion")

    fig = Figure(figsize=(5, 5), dpi=100)

    canvas = FigureCanvasTkAgg(fig, master=branch)
    canvas.draw()

    ax = fig.add_subplot(111, projection="3d")

    RecordDelete = ttk.Button(branch, text="Usuń dane pacjenta", command=lambda: deleteRecord(imieNazwisko))
    RecordDelete.grid(row=9, column=0)

    for plot in range(len(plotsArray)):
        # parsing
        print("eeeee")
        # print(plotsArray[plot])
        pointString = plotsArray[plot]
        pointString = str(pointString)
        pointString = pointString.lstrip("('").rstrip(",)")
        pointsParsed = pointString.split(";")  # do it porperly tomorow
        print(pointsParsed)

        for i in range(9):
            pointsParsedSeparate = pointsParsed[i].split(",")
            points[0, i] = pointsParsedSeparate[0]
            points[1, i] = pointsParsedSeparate[1]
            points[2, i] = pointsParsedSeparate[2]

        print(points)
        # PLOT GOES HEREEEE
        # /////////just copied

        ax.plot(points[0], points[1], points[2])
        ax.scatter(points[0], points[1], points[2])

        canvas.get_tk_widget().grid(row=1, rowspan=8, column=2)
        # //////////////////

        NameLabel = ttk.Label(branch, text=imieNazwisko)
        NameLabel.grid(row=0, column=2)

        # Dates
        prettyDate = str(czasArray[plot])
        prettyDate = prettyDate.lstrip("{('")
        prettyDate = prettyDate[:len(prettyDate) - 10]
        DateLabel = ttk.Label(branch, text=prettyDate)

        DateLabel.config(background=colors[plot])  # idk how many plots this can support, my bet is 10, this is just for testing
        DateLabel.grid(row=0, column=plot + 3)


        # Distances
        DistancesLabel = ttk.Label(branch, text=distances[0])
        DistancesLabel.grid(row=1, column=plot + 3)
        DistancesLabel = ttk.Label(branch, text=distances[1])
        DistancesLabel.grid(row=2, column=plot + 3)
        DistancesLabel = ttk.Label(branch, text=distances[2])
        DistancesLabel.grid(row=3, column=plot + 3)
        DistancesLabel = ttk.Label(branch, text=distances[3])
        DistancesLabel.grid(row=4, column=plot + 3)
        DistancesLabel = ttk.Label(branch, text=distances[4])
        DistancesLabel.grid(row=5, column=plot + 3)
        DistancesLabel = ttk.Label(branch, text=distances[5])
        DistancesLabel.grid(row=6, column=plot + 3)
        DistancesLabel = ttk.Label(branch, text=distances[6])
        DistancesLabel.grid(row=7, column=plot + 3)
        DistancesLabel = ttk.Label(branch, text=distances[7])
        DistancesLabel.grid(row=8, column=plot + 3)

        # Delete buttons
        MeasurementDelete = ttk.Button(branch, text=czasArray[plot],
                                       command=lambda: deleteMeasurement(imieNazwisko, czasArray[plot]))
        MeasurementDelete.grid(row=9, column=plot + 3)

    conn.close()

def previewPlot():
    fig = Figure(figsize=(5, 5), dpi=100)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()

    ax = fig.add_subplot(111, projection="3d")

    # ax.plot(points, yline, zline, 'gray')
    ax.plot(points[0], points[1], points[2])
    ax.scatter(points[0], points[1], points[2])
    canvas.get_tk_widget().grid(row=1, column=2)

    # calculating distances between points
    distances = euclid(points)

    # Show distances between points
    DistancesLabel = ttk.Label(root, text=distances[0])
    DistancesLabel.grid(row=8, column=0)
    DistancesLabel = ttk.Label(root, text=distances[1])
    DistancesLabel.grid(row=8, column=1)
    DistancesLabel = ttk.Label(root, text=distances[2])
    DistancesLabel.grid(row=8, column=2)
    DistancesLabel = ttk.Label(root, text=distances[3])
    DistancesLabel.grid(row=8, column=3)
    DistancesLabel = ttk.Label(root, text=distances[4])
    DistancesLabel.grid(row=8, column=4)
    DistancesLabel = ttk.Label(root, text=distances[5])
    DistancesLabel.grid(row=8, column=5)
    DistancesLabel = ttk.Label(root, text=distances[6])
    DistancesLabel.grid(row=8, column=6)
    DistancesLabel = ttk.Label(root, text=distances[7])
    DistancesLabel.grid(row=8, column=7)


# Set up usb connection
def connect(portg):
    global ser
    global connected

    port = portg[0:4]

    # this is dogshit slow, but at least it works
    # needs to be fixed later
    ser = serial.Serial(port, 115200, timeout=100)
    ser.flushInput()
    connected = 1

# Get point positions over usb
def getUSB():
    index = -1
    # transmition too slow to get all the points,
    # fix: decrease delay in board firmware

    for i in range(18):

        # recieve shit from the board over USB
        data = ser.readline()
        decoded = data.decode('utf8')
        # print(decoded, end = '')

        if "," in decoded:
            index += 1
            separate = decoded.split(",")
            points[0, index] = int(separate[0])
            points[1, index] = int(separate[1])
            points[2, index] = int(separate[2])

        if "BEGIN" in decoded:
            index = -1

    # ser.close()
    print(points)
    previewPlot()

# Get x, y of one arm for showcase purposes
def getUSBpokaz():

    # CHECK THIS FOR OVERHEAD
    # this has to get more than one line, because readline stops at \n, but starts wherever, so before it was
    # getting a random amount of bytes from the back of a packet
    data = ser.readlines(16)

    print(data[1])
    decoded = data[1].decode('utf8')
    if "," in decoded:
        separate = decoded.split(",")
        print(separate)
        if separate[0] != '' and separate[1][0] != '':
            points[0, 0] = int(separate[0]) / int(Calibration.get())
            points[1, 0] = int(separate[1]) / int(Calibration.get())

    # check this
    ser.flushInput()
    # ser.close()
    print(points)
    previewPlot()


def portSelect(choice):
    port = choice


# toolbar attempt, didn't work
"""
toolbar = Menu(root)
root.config(menu=toolbar)

setPort = Listbox(toolbar)


ports = p.comports()
#portList = []
for i in ports:
    setPort.insert(END, i)
print(setPort)
#settings.
toolbar.add_cascade(label="Port", menu=setPort)

setPort.grid(row=0, column = 7)
"""
# LOOP

if(connected == 0):
    portChoice = ttk.Combobox(root, width=25, value=p.comports())
    portChoice.grid(row = 0, column = 5)
    connectButton = ttk.Button(root, text = "connect!", command = lambda: connect(portChoice.get()))
    connectButton.grid(row = 0, column=6)

testButton = ttk.Button(root, text="pobierz koordynaty", command=getUSBpokaz)
testButton.grid(row=0, column=2)

# serch for patient
conn = sqlite3.connect('patients.db')
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS patients (
       imie text,
       nazwisko text,
       points text,
       czas text
   )""")

conn = sqlite3.connect('patients.db')
c = conn.cursor()
c.execute("SELECT imie FROM patients")
imiona = c.fetchall()  ############################################################################################
c.execute("SELECT nazwisko FROM patients")
nazwiska = c.fetchall()
imionaNazwiska = []
for i in range(len(imiona)):
    imionaNazwiska.append(imiona[i] + nazwiska[i])
conn.commit()
SearchField = ttk.Combobox(root, width=25, value=imionaNazwiska)
SearchField.grid(row=0, column=1)
SearchButton = ttk.Button(root, text="Szukaj", command=lambda: readFromDB(SearchField.get()))
SearchButton.grid(row=1, column=1, sticky=N)

# record data
ImieLabel = ttk.Label(root, text="Imię:")
ImieLabel.grid(row=4, column=1, sticky=E)
ImieField = ttk.Entry(root, width=40)
ImieField.grid(row=4, column=2)
NazwiskoLabel = ttk.Label(root, text="Nazwisko:")
NazwiskoLabel.grid(row=5, column=1, sticky=E)
NazwiskoField = ttk.Entry(root, width=40)
NazwiskoField.grid(row=5, column=2)

# save button
saveButton = ttk.Button(root, text="Zapisz",
                        command=lambda: writeToDB(ImieField.get(), NazwiskoField.get(), concatenation()))
saveButton.grid(row=6, column=2)

# Rudimentary calibration
Calibration = ttk.Entry(root, width=40)
Calibration.insert(0,"300")
Calibration.grid(row = 7, column = 1)
CalibrationLabel = ttk.Label(root, text="<-- dzielnik do kalibracji")
CalibrationLabel.grid(row=7, column=2, sticky=W)


root.mainloop()
