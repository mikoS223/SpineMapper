# UI
import math
import tkinter as tk
from tkinter.messagebox import askyesno
from tkinter import ttk
from tkcalendar import DateEntry
from tkinter import filedialog

import numpy
from ttkthemes import ThemedTk

# Arrays
import numpy as np

# Plots
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Usb
import serial
import serial.tools.list_ports as p

# Database
import sqlite3

# Time
from datetime import datetime

# Profiling
import cProfile
import pstats

# Printout
from fpdf import FPDF

# serialization

import pickle

class PDF(FPDF):
    pass

now = datetime.now()


# performance
profiler = cProfile.Profile()
profiler.enable()

connected = 0

# zeroing array
zeroing = np.zeros([3, 6])

# tip arm radious (future functionality)
radious = 65

# points before zeroing
rawPoints = np.zeros([3, 6])

# 1:1 values from USB
intake = np.zeros([3, 6])

# rotary encoder callibration values
try:
    with open('rotaryCallibrationData.pickle', 'rb') as f:
        zeroAngle = pickle.load(f)
except FileNotFoundError:
    zeroAngle = np.zeros([6])
print(zeroAngle)

# measurement array
points = np.zeros([3, 6])
distances = np.zeros([5])

# GRAPH COLORS FOR DISPLAYING SAVED MEASUREMENTS
# getting default color progression from matplotlib
# colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]


# separate[0]-> x separate[1]-> y separate[2]-> z,
# this variable is used for parsing coordinates from USB packets
separate = []

# tkinter window init
root = ThemedTk()
root.wm_title("Pomiar kręgosłupa")

# full screen
root.state('zoomed')

# scaling with screen resolution (just both plots)
root.columnconfigure(2, weight=1)
root.columnconfigure(4, weight=1)
root.rowconfigure(1, weight=1)

# Widgets style
style = ttk.Style(root)
style.theme_use("yaru")

style.configure('TFrame', background='white')
root.configure(background='white')
style.configure('TLabel', background='white')

# basically just takes a snapshot of current points and adds some offsets
def zeroPoints():
    global zeroing
    # zeroing[0][0] = 0
    for i in range(6):
        zeroing[0][i] = rawPoints[0][i]
        zeroing[2][i] = rawPoints[2][i]
    # print("ZEROED")

    # offsets !THIS IS MACHINE-SPECIFIC AND NEEDS TO BE SOLVED!
    # offsets for z
    zeroing[2][1] -= 67.7 - 6
    zeroing[2][2] -= 121.62
    zeroing[2][3] -= 182.2
    zeroing[2][4] -= 242.5
    zeroing[2][5] -= 303.32

    # offsets for x
    zeroing[0][0] -= 10.6
    zeroing[0][1] -= 10.4
    zeroing[0][2] -= 1.9
    zeroing[0][3] -= 3.4
    zeroing[0][4] -= 0
    zeroing[0][5] -= 2.8

    print(zeroing)
    # statusBar["text"] = "wyzerowano"


# delete functionality for a future data base, i'm leaving it here for possible future use
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


# delete a whole personal record, also for possible future use
def deleteRecord(imieNazwisko):
    if askyesno(title='Potwierdzenie', message='Usunąć wszystkie dane pacenta?'):
        imieNazwiskoSplit = imieNazwisko.split(" ")
        conn = sqlite3.connect('patients.db')
        c = conn.cursor()
        c.execute("DELETE FROM patients WHERE imie = (?) AND nazwisko = (?)", imieNazwiskoSplit)
        conn.commit()


def euclid3d(currentPoints):
    distances = np.zeros([5])
    pointsT = currentPoints.transpose()

    for i in range(5):
        distances[i] = round(np.linalg.norm(pointsT[i] - pointsT[i + 1]), 1)

    return distances

# calculate a 2d euclidean distance between 2 points
def euclid2d(xaxis, yaxis):
    distances = np.zeros([5])
    for i in range(5):
        distances[i] = round(numpy.sqrt((xaxis[i] - xaxis[i + 1]) ** 2 + (yaxis[i] - yaxis[i + 1]) ** 2), 1)

    return distances

# this was used for testing and saving to database
def concatenation():
    concat = ""
    for i in range(6):
        concat += str(points[0, i]) + "," + str(points[1, i]) + "," + str(points[2, i]) + ";"
    return concat

# save to database, unused for now, left here for possible future reference
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

# the actual function that draws the two plots visible when calling testpoints or taking a measurement
def plotPoints2d(pointsx, pointsy, window, saveAs, xlabel):
    # calculating distances between points
    distances = euclid2d(pointsx, pointsy)
    print("x")
    print(pointsx)
    print("y")
    print(pointsy)

    # plot size can be controlled form here, the "layot=constrained" here is because it was getting clipped without it
    figxy = Figure(figsize=(6, 12), dpi=100, layout="constrained")

    canvas = FigureCanvasTkAgg(figxy, master=window)
    canvas.draw()

    ax = figxy.add_subplot(111)

    ax.plot(pointsx, pointsy, 'gray')
    ax.scatter(pointsx, pointsy)

    # set ranges on the x axis of both plots
    if xlabel == 'X':
        ax.set_xlim([0, 250])
    else:
        ax.set_xlim([-70, 70])

    # y axis range for both plots
    ax.set_ylim([-80, 1200])
    ax.set_ylabel('Z', labelpad=-7)
    ax.set_title(xlabel)

    # Show distances between points
    for i in range(5):
        xmidpoint = pointsx[i] + ((pointsx[i + 1] - pointsx[i]) / 2)
        if xlabel == 'X':
            if xmidpoint > 125:
               xmidpoint -= 15
            else:
                xmidpoint += 15

        else:
            if xmidpoint > 0:
                xmidpoint -= 10
            else:
                xmidpoint += 10

        ymidpoint = pointsy[i] + ((pointsy[i + 1] - pointsy[i]) / 2)

        figxy.text(xmidpoint, ymidpoint, distances[i], horizontalalignment='center', verticalalignment='center',
                   transform=ax.transData)

    slope = np.zeros([5])
    angle = np.zeros([5])

    # display degrees on plots
    for i in range(5):
        slope[i] = ((pointsy[i + 1] - pointsy[i]) / (pointsx[i + 1] - pointsx[i]))
        # degrees from horizontal
        angle[i] = round(90 - (math.degrees(math.atan(slope[i]))), 2)
        # degrees from vertical
        # angle[i] = round(math.degrees(math.atan(slope[i])),2)
        figxy.text(pointsx[i] + 20, pointsy[i] + 20, str(angle[i]) + u'\N{DEGREE SIGN}', horizontalalignment='center', verticalalignment='center',
                   transform=ax.transData)
        # ax.plot([pointsx[i], pointsx[i]+10], [pointsy[i]+10,  pointsy[i] + 10], color="black")

    figxy.savefig(saveAs)
    return canvas.get_tk_widget()


# another database functionality that i'm leaving here for future reference
# this was actualy another window that would open and compare all of a patients measurements
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

        for i in range(6):
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

        DateLabel.config(
            background=colors[plot])  # idk how many plots this can support, my bet is 10, this is just for testing
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


# Set up usb connection
def connect(portg):
    global ser
    global connected

    port = portg[0:4]

    # slow,
    # needs to be fixed later
    ser = serial.Serial(port, 115200, timeout=100)
    ser.flushInput()
    connected = 1
   # if (connected == 1):
        # statusBar["text"] = "Connected to " + portg[0:4]

def clearPersonalInfo():
    ImieField.delete(0, tk.END)
    NazwiskoField.delete(0, tk.END)
    PeselField.delete(0, tk.END)
    NotesField.delete(1.0, tk.END)

def rotaryCalibration():
    index = -1
    ser.write(b'a')

    data = ser.readlines(145)

    # print(data)
    for i in range(7):

        decoded = data[i].decode('utf8')

        if ";" in decoded:
            index += 1
            separate = decoded.split(";")
            # print(separate)
            try:
                separate[0] = str(separate[0]).replace('.', '')
                separate[1] = str(separate[1]).replace('.', '')
                separate[2] = str(separate[2]).replace('.', '')
            except ValueError:
                print("Something tried to insert a wrong value into separate")
            except IndexError:
                print("index out of range")
                # print(separate[0])
                # print(separate[1])
                # print(separate[2])


            intake[1, index] = int(separate[1])  # / int(Calibration.get())
            zeroAngle[index] = 1024 + intake[1, index]


        if "BEGIN" in decoded:
            index = -1

        # check this
    ser.flushInput()

    with open('rotaryCallibrationData.pickle', 'wb') as f:
        pickle.dump(zeroAngle, f)


# Get points over usb
# this works, but has to be cleaned up
def getUSBpokaz():
    index = -1
    ser.write(b'a')


    data = ser.readlines(145)

    # print(data)
    for i in range(7):

        decoded = data[i].decode('utf8')

        if ";" in decoded:
            index += 1
            separate = decoded.split(";")
            # print(separate)
            try:
                separate[0] = str(separate[0]).replace('.', '')
                separate[1] = str(separate[1]).replace('.', '')
                separate[2] = str(separate[2]).replace('.', '')
            except ValueError:
                print("Something tried to insert a wrong value into separate")
            except IndexError:
                print("index out of range")
                # print(separate[0])
                # print(separate[1])
                # print(separate[2])


            intake[0, index] = int(separate[0])  # / int(Calibration.get())
            rawPoints[0, index] = intake[0, index] * (3.2 / 18)
            intake[1, index] = int(separate[1])  # / int(Calibration.get())
            intake[1,index] = intake[1, index] - zeroAngle[index]
            if intake[1, index] < 0:
                intake[1, index] = intake[1,index] + 4096

            rawPoints[1, index] = radious * math.cos(math.radians(intake[1, index] * (360 / 4096)))

            intake[2, index] = int(separate[2])  # / int(Calibration.get())
            rawPoints[2, index] = intake[2, index] * (3.2 / 18)

        if "BEGIN" in decoded:
            index = -1

        # check this
    ser.flushInput()
    # ser.close()
    # print(rawPoints)
    # zeroing = rawPoints

    # subtracts zeroing matrix form points pulled from usb
    points = np.subtract(rawPoints, zeroing)
    for i in range(6):
        points[2][i] = points[2][i] + (radious * math.sin(math.radians(intake[1, i] * (360 / 4096))))
        print("/////////////")
        print(radious * math.sin(math.radians(intake[1, i] * (360 / 4096))))
    print("points:")
    print(points)
    print("zeroing array:")
    print(zeroing)
    # print(points[0])
    # print(points[2])
    # previewPlot()
    print("xz:")

    # display the plots
    xzprojection = plotPoints2d(points[0], points[2], root, 'xzprojection.png', 'X')
    xzprojection.grid(row=1, column=1, rowspan=3, columnspan=3, sticky="NS", pady=20)
    print("yz:")
    yzprojection = plotPoints2d(points[1], points[2], root, 'yzprojection.png', 'Y')
    yzprojection.grid(row=1, column=4, rowspan=3, columnspan=3, sticky="NS", pady=20, padx=(0,20))

    # display datetime of measurement
    now = datetime.now()
    DataPomiaruField.delete(0,tk.END)
    DataPomiaruField.insert(0, now.strftime("%d/%m/%Y %H:%M:%S"))



def portSelect(choice):
    port = choice

# save both figures and personal info to a pdf file
def saveAsPdf(imie, nazwisko, dataUrodzenia, pesel, dataPomiaru, opis):
    # root.configure(cursor="wait")
    # root.update()
    # statusBar["text"] = "Zapisywanie pliku pdf..." # + str(win32print.GetDefaultPrinter()) + "..."

    pdfDestination = filedialog.asksaveasfilename(title="Select a file", filetypes=(
        [("PDF file", "*.pdf")]))
    print(pdfDestination + ".pdf")

    pdf = PDF('L')
    pdf.add_font("ArialUni", style="", fname="fonts\ArialUnicodeMS.ttf", uni=True)
    pdf.add_page()
    pdf.set_xy(25, 10)
    pdf.image("xzprojection.png", h=175)
    pdf.set_xy(120, 10)
    pdf.image("yzprojection.png", h=175)
    pdf.set_font("ArialUni")
    pdf.text(220, 50, txt=imie)
    pdf.text(220, 60, txt=nazwisko)
    pdf.text(220, 70, txt=str(dataUrodzenia))
    pdf.text(220, 80, txt=pesel)
    pdf.text(220, 90, txt=dataPomiaru)
    pdf.set_xy(220, 110)
    pdf.multi_cell(75, 5, txt=opis)


    pdf.output(pdfDestination + ".pdf", 'F')

    # root.configure(cursor="")
    # PRINTING CANCELLED
    # try:

    # win32api.ShellExecute(0, "print", os.path.abspath("pomiar.jpg"), None, ".", 0)
    # except:
    #     statusBar["text"] = "Błąd w drukowaniu"
    # else:
    #     statusBar["text"] = "Poprawne drukowanie"

# generate some test values and draw graphs from that
def testPoints():
    for i in range(6):
        points[0, i] = 100 + i * 10
        points[1, i] = (i - 2) * 5
        points[2, i] = (i + 4) * 100

    print(points)
    # previewPlot()
    xzprojection = plotPoints2d(points[0], points[2], root, 'xzprojection.png', 'X')
    xzprojection.grid(row=1, column=2, rowspan=3, columnspan=2, sticky="NS", pady=20)
    yzprojection = plotPoints2d(points[1], points[2], root, 'yzprojection.png', 'Y')
    yzprojection.grid(row=1, column=4, rowspan=3, columnspan=3, sticky="NS", pady=20, padx=(0, 20))
    # statusBar["text"] = "wygenerowano punkty testowe"

    # display datetime of measurement
    now = datetime.now()
    DataPomiaruField.delete(0, tk.END)
    DataPomiaruField.insert(0, now.strftime("%d/%m/%Y %H:%M:%S"))


# MENU BAR
menubar = tk.Menu(root)
root.config(menu=menubar)

fileMenu = tk.Menu(menubar, tearoff=0)
# menubar.add_cascade(label="Plik", menu=fileMenu)
menubar.add_command(label="Zapisz jako pdf",
                     command=lambda: saveAsPdf(ImieField.get(), NazwiskoField.get(), DataUrodzeniaSelector.get_date(),
                                               PeselField.get(), DataPomiaruField.get(), NotesField.get("1.0", "end")))
# fileMenu.add_command(label="Zapisz", command=lambda: writeToDB(ImieField.get(), NazwiskoField.get(), concatenation()))
ustawieniaMenu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Ustawienia", menu=ustawieniaMenu)

ustawieniaMenu.add_command(label="Punkty testowe", command=testPoints)

ustawieniaMenu.add_command(label="Kalibracja obrotu", command=lambda: rotaryCalibration())

# menubar.add_command(label="Connect", command=lambda: connect(portChoice.get()))

setPort = tk.Listbox(menubar)
ports = p.comports()
#portList = []
for i in ports:
    setPort.insert(tk.END, i)
print(setPort)
#settings.
# menubar.add_cascade(label="Port", menu=setPort)

#setPort.grid(row=0, column = 7)


# MAINLOOP
if connected == 0:
    portChoice = ttk.Combobox(root, value=p.comports())
    portChoice.grid(row=0, column=5)
    connectButton = ttk.Button(root, text="Połącz", command=lambda: connect(portChoice.get()))
    connectButton.grid(row=0, column=6)

getPointsButton = ttk.Button(root, text="Wykonaj pomiar", command=getUSBpokaz)
getPointsButton.grid(row=0, column=1, sticky=tk.E, padx=(0, 40), ipadx=5)

# connect to database
# conn = sqlite3.connect('patients.db')
# c = conn.cursor()
# c.execute("""CREATE TABLE IF NOT EXISTS patients (
#        imie text,
#        nazwisko text,
#        points text,
#        czas text
#    )""")
#
# conn = sqlite3.connect('patients.db')
# c = conn.cursor()
# c.execute("SELECT imie FROM patients")
# imiona = c.fetchall()
# c.execute("SELECT nazwisko FROM patients")
# nazwiska = c.fetchall()
# imionaNazwiska = []
# for i in range(len(imiona)):
#   imionaNazwiska.append(imiona[i] + nazwiska[i])
# conn.commit()
# SearchField = ttk.Combobox(root, width=25, value=imionaNazwiska)
# SearchField.grid(row=0, column=1)
# SearchButton = ttk.Button(root, text="Szukaj", command=lambda: readFromDB(SearchField.get()))
# SearchButton.grid(row=1, column=1, sticky=N)

# PERSONAL INFO
personalInfoFrame = ttk.Frame(root)
personalInfoFrame.grid(row=1, column=0, padx=20, columnspan=2)

ImieLabel = ttk.Label(personalInfoFrame, text="Imię:")
ImieLabel.grid(row=0, column=0, sticky="NE")
ImieField = ttk.Entry(personalInfoFrame, width=40, )
ImieField.grid(row=0, column=1, padx=20)
NazwiskoLabel = ttk.Label(personalInfoFrame, text="Nazwisko:")
NazwiskoLabel.grid(row=1, column=0, sticky="NE")
NazwiskoField = ttk.Entry(personalInfoFrame, width=40)
NazwiskoField.grid(row=1, column=1)

DataUrodzeniaLabel = ttk.Label(personalInfoFrame, text="Data urodzenia:")
DataUrodzeniaLabel.grid(row=2, column=0, sticky="NE")
DataUrodzeniaSelector = DateEntry(personalInfoFrame, selectmode='day', year=2000, month=1, day=1)
DataUrodzeniaSelector.grid(row=2, column=1, sticky="W", padx=20)

PeselLabel = ttk.Label(personalInfoFrame, text="PESEL:")
PeselLabel.grid(row=3, column=0)
PeselField = ttk.Entry(personalInfoFrame, width=40)
PeselField.grid(row=3, column=1)
DataPomiaruLabel = ttk.Label(personalInfoFrame, text="Data pomiaru:")
DataPomiaruLabel.grid(row=4, column=0)
DataPomiaruField = ttk.Entry(personalInfoFrame, width=40)
DataPomiaruField.grid(row=4, column=1)
DataPomiaruField.insert(0, now.strftime("%d/%m/%Y %H:%M:%S"))
NotesLabel = ttk.Label(personalInfoFrame, text="Opis:")
NotesLabel.grid(row=5, column=0)
NotesField = tk.Text(personalInfoFrame, width=30, wrap=tk.WORD)
NotesField.grid(row=5, column=1)

ClearPersonalInfoButton = ttk.Button(personalInfoFrame, text="Wyczyść", command=clearPersonalInfo)
ClearPersonalInfoButton.grid(row=6, column=0, columnspan=2)

# Zeroing
zeroButton = ttk.Button(root, text="Pozycja zerowa", command=zeroPoints)
zeroButton.grid(row=0, column=0, sticky=tk.E, padx=(110, 0), ipadx=5)

# statusBar = ttk.Label(root, text="status", border=1, relief=tk.SUNKEN, anchor="se")
# statusBar.grid(rowspan=8, columnspan=10, sticky="SWE")

root.mainloop()

# terminate profiling
profiler.disable()

# generate report to console
stats = pstats.Stats(profiler).sort_stats('cumtime')
stats.print_stats()
