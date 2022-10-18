# good god, this is beyond clusterfucked
# how am i even allowed to write code
from tkinter import *
from tkinter.messagebox import askyesno
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import serial
import sqlite3
import datetime
from scipy.spatial import distance

# usb port !!!!!!!!!PLATFORM SPECIFIC!!!!!!!
port = "/dev/ttyUSB0"

# some initialization bullshit for USB communication, idk

# measurement array
points = np.zeros([3, 9])
distances = np.zeros([8])

# getting default color progression from matplotlib

colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]


# indexer for rods


# separate[0]-> x separate[1]-> y separate[2]-> z,
# this variable is used for parsing coordinates from USB packets
separate = []

# tkinter window init shit
root = Tk()
root.wm_title("Spine Mapper")

def deleteMeasurement(imieNazwisko, date): # DELETES WRONG MEASUREMENT
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
    if askyesno(title='Potwierdzenie', message='Usunąć dane pacenta?'):
        imieNazwiskoSplit = imieNazwisko.split(" ")
        conn = sqlite3.connect('patients.db')
        c = conn.cursor()
        c.execute("DELETE FROM patients WHERE imie = (?) AND nazwisko = (?)", imieNazwiskoSplit)
        conn.commit()


def euclid(currentPoints):
    distances = np.zeros([8])
    pointsT = currentPoints.transpose()
    for i in range(8):
        distances[i] = distance.euclidean(pointsT[i], pointsT[i + 1])

    return distances


# this is horrendous
def concatenation():
    concat = ""
    for i in range(9):  # this is so wrong
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
    # this is just plain ugly, i'm telling myself
    # i'll make it better once it works, but
    # let's be honest, i probably won't

    # another tkinter window
    branch = Toplevel()
    branch.wm_title("Spine Comparasion")

    # hmmmmmmmmmmmmmmok

    fig = Figure(figsize=(5, 5), dpi=100)

    canvas = FigureCanvasTkAgg(fig, master=branch)
    canvas.draw()

    ax = fig.add_subplot(111, projection="3d")

    RecordDelete = Button(branch, text="Usuń dane pacjenta", command=lambda: deleteRecord(imieNazwisko))
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

        NameLabel = Label(branch, text=imieNazwisko)
        NameLabel.grid(row=0, column=2)

        prettyDate = str(czasArray[plot])
        prettyDate = prettyDate.lstrip("{('")
        prettyDate = prettyDate[:len(prettyDate)-10]
        DateLabel = Label(branch, text=prettyDate)
        DateLabel.config(bg=colors[plot]) # idk how many plots this can support, my bet is 10, this is just for testing
        DateLabel.grid(row=0, column=plot + 3)

        distances = euclid(points)

        DistancesLabel = Label(branch, text=distances[0])
        DistancesLabel.grid(row=1, column=plot + 3)
        DistancesLabel = Label(branch, text=distances[1])
        DistancesLabel.grid(row=2, column=plot + 3)
        DistancesLabel = Label(branch, text=distances[2])
        DistancesLabel.grid(row=3, column=plot + 3)
        DistancesLabel = Label(branch, text=distances[3])
        DistancesLabel.grid(row=4, column=plot + 3)
        DistancesLabel = Label(branch, text=distances[4])
        DistancesLabel.grid(row=5, column=plot + 3)
        DistancesLabel = Label(branch, text=distances[5])
        DistancesLabel.grid(row=6, column=plot + 3)
        DistancesLabel = Label(branch, text=distances[6])
        DistancesLabel.grid(row=7, column=plot + 3)
        DistancesLabel = Label(branch, text=distances[7])
        DistancesLabel.grid(row=8, column=plot + 3)

        MeasurementDelete = Button(branch, text=czasArray[plot], command=lambda: deleteMeasurement(imieNazwisko, czasArray[plot]))
        MeasurementDelete.grid(row=9, column=plot+3)


    conn.close()


# measurement points preview
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

    # legend

    DistancesLabel = Label(root, text=distances[0])
    DistancesLabel.grid(row=1, column=3)
    DistancesLabel = Label(root, text=distances[1])
    DistancesLabel.grid(row=2, column=3)
    DistancesLabel = Label(root, text=distances[2])
    DistancesLabel.grid(row=3, column=3)
    DistancesLabel = Label(root, text=distances[3])
    DistancesLabel.grid(row=4, column=3)
    DistancesLabel = Label(root, text=distances[4])
    DistancesLabel.grid(row=5, column=3)
    DistancesLabel = Label(root, text=distances[5])
    DistancesLabel.grid(row=6, column=3)
    DistancesLabel = Label(root, text=distances[6])
    DistancesLabel.grid(row=7, column=3)
    DistancesLabel = Label(root, text=distances[7])
    DistancesLabel.grid(row=8, column=3)


def getUSB():
    index = -1
    # transmition too slow to get all the points,
    # fix: decrease delay in board firmware

    # this is dogshit slow, but at least it works
    # needs to be fixed later
    ser = serial.Serial(port, 115200, timeout=100)
    ser.flushInput()
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

    ser.close()
    print(points)
    previewPlot()


# LOOP
testButton = Button(root, text="pobierz koordynaty", command=getUSB)
testButton.grid(row=0, column=2)

# serch for patient
SearchField = Entry(root, width=25)
SearchField.grid(row=0, column=1)
SearchButton = Button(root, text="Szukaj", command=lambda: readFromDB(SearchField.get()))
SearchButton.grid(row=1, column=1)

# record data
ImieLabel = Label(root, text="Imię:")
ImieLabel.grid(row=4, column=1, sticky=E)
ImieField = Entry(root, width=40)
ImieField.grid(row=4, column=2)
NazwiskoLabel = Label(root, text="Nazwisko:")
NazwiskoLabel.grid(row=5, column=1, sticky=E)
NazwiskoField = Entry(root, width=40)
NazwiskoField.grid(row=5, column=2)

# save button
saveButton = Button(root, text="Zapisz",
                    command=lambda: writeToDB(ImieField.get(), NazwiskoField.get(), concatenation()))
saveButton.grid(row=6, column=2)

root.mainloop()