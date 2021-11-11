from bokeh.models.sources import ColumnDataSource
import pandas as pd

from bokeh.layouts import column, row
from bokeh.models import Panel, Tabs, Select, Button
from bokeh.plotting import curdoc, figure
import pandas as pd
import serial
import serial.tools.list_ports
from dataThread import DataReceiver
from queue import Queue
import queue
import numpy as np

DEFAULT_DATA = pd.DataFrame({"TIME": 0, "ACCELX": 0, "ACCELY": 0, "ACCELZ": 0, "GYROX": 0, "GYROY": 0, "GYROZ": 0, "MAGX": 0, "MAGY": 0, "MAGZ": 0,}, index=[0])


class DATA:
    TIME = "TIME"
    ACCELX = "ACCELX"
    ACCELY = "ACCELY"
    ACCELZ = "ACCELZ"
    GYROX = "GYROX"
    GYROY = "GYROY"
    GYROZ = "GYROZ"
    MAGX = "MAGX"
    MAGY = "MAGY"
    MAGZ = "MAGZ"
    # POSX = "POSX"
    # POSY = "POSY"
    # POSZ = "POSZ"
    # TIME = "TIME"
    COLUMNS = ["ACCELX", "ACCELY", "ACCELZ", "GYROX", "GYROY", "GYROZ", "MAGX", "MAGY", "MAGZ"]


class PayloadUI:
    def __init__(self) -> None:
        self.dataSource = ColumnDataSource(DEFAULT_DATA)
        self.currentPosSource = ColumnDataSource(pd.DataFrame(columns=["X", "Y"]))
        self.dataQue_ = Queue(maxsize=6)
        self.receiver_ = DataReceiver(None, None)
        self._callbackId = None
        self.rawData = DEFAULT_DATA

        self.time = np.empty((0,))
        self.accelX = np.empty((0,))
        self.accelY = np.empty((0,))
        self.accelZ = np.empty((0,))
        self.gyroX = np.empty((0,))
        self.gyroY = np.empty((0,))
        self.gyroZ = np.empty((0,))
        self.magX = np.empty((0,))
        self.magY = np.empty((0,))
        self.magZ = np.empty((0,))
        self._index = 0

        self.nedPlot = figure(title="Position", sizing_mode="stretch_both", x_axis_label="Time", y_axis_label="Meters")
        self.positionTab = Panel(child=self.nedPlot, title="Position")

        self.accelPlot = figure(title="Accelerometer", sizing_mode="stretch_both", x_axis_label="Time", y_axis_label="g")
        self.gyroPlot = figure(title="Gyrometer", sizing_mode="stretch_both", x_axis_label="Time", y_axis_label="dps")
        self.magPlot = figure(title="Magnetometer", sizing_mode="stretch_both", x_axis_label="Time", y_axis_label="mGauss")
        self.developerTab = Panel(child=column(self.accelPlot, self.gyroPlot, self.magPlot, sizing_mode="stretch_both"), title="Developer")

        self.startButton = Button(label="Start")
        self.stopButton = Button(label="Stop")
        self.comSelect = Select(title="Com Port")
        self.baudSelect = Select(title="Baud Rate", value="115200", options=[str(rate) for rate in [9600, 115200]])

        self.btnRow = row(self.startButton, self.stopButton, self.comSelect, self.baudSelect)
        self.layout = column(self.btnRow, Tabs(tabs=[self.positionTab, self.developerTab]), sizing_mode="stretch_width")
        self.initialize()

        curdoc().add_root(self.layout)
        curdoc().title = "CRW Payload Team 2021 - 2022"

    def initialize(self) -> None:
        self.nedPlot.circle(x=0, y=0, source=self.currentPosSource)

        self.accelPlot.circle(x=DATA.TIME, y=DATA.ACCELX, color="blue", legend_label="X", source=self.dataSource)
        self.accelPlot.circle(x=DATA.TIME, y=DATA.ACCELY, color="red", legend_label="Y", source=self.dataSource)
        self.accelPlot.circle(x=DATA.TIME, y=DATA.ACCELZ, color="green", legend_label="Z", source=self.dataSource)
        self.accelPlot.legend.click_policy = "hide"

        self.gyroPlot.circle(x=DATA.TIME, y=DATA.GYROX, color="blue", legend_label="X", source=self.dataSource)
        self.gyroPlot.circle(x=DATA.TIME, y=DATA.GYROY, color="red", legend_label="Y", source=self.dataSource)
        self.gyroPlot.circle(x=DATA.TIME, y=DATA.GYROZ, color="green", legend_label="Z", source=self.dataSource)
        self.gyroPlot.legend.click_policy = "hide"

        self.magPlot.circle(x=DATA.TIME, y=DATA.MAGX, color="blue", legend_label="X", source=self.dataSource)
        self.magPlot.circle(x=DATA.TIME, y=DATA.MAGY, color="red", legend_label="Y", source=self.dataSource)
        self.magPlot.circle(x=DATA.TIME, y=DATA.MAGZ, color="green", legend_label="Z", source=self.dataSource)
        self.magPlot.legend.click_policy = "hide"

        self.startButton.on_click(self.connect)
        self.stopButton.on_click(self.stop)

        self.updatePorts()

    def updatePorts(self) -> None:
        portsAvailble = []
        ports = serial.tools.list_ports.comports()

        if len(ports) == 0 or ports is None:
            print("No com ports found, check connections")
        else:
            for port, desc, hwid in sorted(ports):
                print("{}: {} [{}]".format(port, desc, hwid))
                portsAvailble.append(port)
        self.comSelect.options = portsAvailble
        self.comSelect.value = portsAvailble[-1]

    def connect(self):
        if self.receiver_.is_alive():
            return

        comPort = self.comSelect.value
        baudRate = float(self.baudSelect.value)
        if comPort == "":
            print("Can't create connection without a known com port. Current Port: {:s}".format(comPort))

        else:
            self.serialHandler_ = serial.Serial(port=comPort, baudrate=baudRate)

        self.receiver_ = DataReceiver(self.serialHandler_, self.dataQue_)
        self.receiver_.start()
        self._callbackId = curdoc().add_periodic_callback(self.receiveData, 10)
        print("Connection Initiated")

    def stop(self) -> None:
        self.receiver_.kill()
        self.serialHandler_.close()
        if self._callbackId is not None:
            curdoc().remove_periodic_callback(self._callbackId)
            self._callbackId = None

    def receiveData(self) -> None:
        noData = False
        while not noData:
            try:
                data = self.dataQue_.get(False)
            except queue.Empty:
                noData = True
            else:
                if self.time.shape[0] >= 1000:
                    self.time = np.roll(self.time, len(data[0]))
                    self.accelX = np.roll(self.accelX, len(data[0]))
                    self.accelY = np.roll(self.accelY, len(data[0]))
                    self.accelZ = np.roll(self.accelZ, len(data[0]))
                    self.gyroX = np.roll(self.gyroX, len(data[0]))
                    self.gyroY = np.roll(self.gyroY, len(data[0]))
                    self.gyroZ = np.roll(self.gyroZ, len(data[0]))
                    self.magX = np.roll(self.magX, len(data[0]))
                    self.magY = np.roll(self.magY, len(data[0]))
                    self.magZ = np.roll(self.magZ, len(data[0]))

                    self.time = np.append(self.time[: -len(data[0])], np.array(data[0]))
                    self.accelX = np.append(self.accelX[: -len(data[1])], data[1])
                    self.accelY = np.append(self.accelY[: -len(data[2])], data[2])
                    self.accelZ = np.append(self.accelZ[: -len(data[3])], data[3])
                    self.gyroX = np.append(self.gyroX[: -len(data[4])], data[4])
                    self.gyroY = np.append(self.gyroY[: -len(data[5])], data[5])
                    self.gyroZ = np.append(self.gyroZ[: -len(data[6])], data[6])
                    self.magX = np.append(self.magX[: -len(data[7])], data[7])
                    self.magY = np.append(self.magY[: -len(data[8])], data[8])
                    self.magZ = np.append(self.magZ[: -len(data[9])], data[9])
                else:
                    self.time = np.append(self.time, np.array(data[0]))
                    self.accelX = np.append(self.accelX, data[1])
                    self.accelY = np.append(self.accelY, data[2])
                    self.accelZ = np.append(self.accelZ, data[3])
                    self.gyroX = np.append(self.gyroX, data[4])
                    self.gyroY = np.append(self.gyroY, data[5])
                    self.gyroZ = np.append(self.gyroZ, data[6])
                    self.magX = np.append(self.magX, data[7])
                    self.magY = np.append(self.magY, data[8])
                    self.magZ = np.append(self.magZ, data[9])

                indexs = np.arange(0, self.time.shape[0], 1)
                newData = {
                    "index": indexs[:-1],
                    "TIME": self.time[:-1],
                    "ACCELX": self.accelX[:-1],
                    "ACCELY": self.accelY[:-1],
                    "ACCELZ": self.accelZ[:-1],
                    "GYROX": self.gyroX[:-1],
                    "GYROY": self.gyroY[:-1],
                    "GYROZ": self.gyroZ[:-1],
                    "MAGX": self.magX[:-1],
                    "MAGY": self.magY[:-1],
                    "MAGZ": self.magZ[:-1],
                }
                self.dataSource.data.update(newData)


p = PayloadUI()
