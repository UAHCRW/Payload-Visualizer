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
    POSX = "POSX"
    POSY = "POSY"
    POSZ = "POSZ"
    TIME = "TIME"
    COLUMNS = ["ACCELX", "ACCELY", "ACCELZ", "GYROX", "GYROY", "GYROZ", "MAGX", "MAGY", "MAGZ", "POSX", "POSY", "POSZ"]


class PayloadUI:
    def __init__(self) -> None:
        self.dataSource = ColumnDataSource(pd.DataFrame(columns=DATA.COLUMNS))
        self.currentPosSource = ColumnDataSource(pd.DataFrame(columns=["X", "Y"]))
        self.dataQue_ = Queue(maxsize=6)
        self.receiver_ = DataReceiver(None, None)
        self._callbackId = None

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

        self.accelPlot.line(x=DATA.TIME, y=DATA.ACCELX, color="blue", legend_label="X", source=self.dataSource)
        self.accelPlot.line(x=DATA.TIME, y=DATA.ACCELY, color="red", legend_label="Y", source=self.dataSource)
        self.accelPlot.line(x=DATA.TIME, y=DATA.ACCELZ, color="green", legend_label="Z", source=self.dataSource)
        self.accelPlot.legend.click_policy = "hide"

        self.gyroPlot.line(x=DATA.TIME, y=DATA.GYROX, color="blue", legend_label="X", source=self.dataSource)
        self.gyroPlot.line(x=DATA.TIME, y=DATA.GYROY, color="red", legend_label="Y", source=self.dataSource)
        self.gyroPlot.line(x=DATA.TIME, y=DATA.GYROZ, color="green", legend_label="Z", source=self.dataSource)
        self.gyroPlot.legend.click_policy = "hide"

        self.magPlot.line(x=DATA.TIME, y=DATA.MAGX, color="blue", legend_label="X", source=self.dataSource)
        self.magPlot.line(x=DATA.TIME, y=DATA.MAGY, color="red", legend_label="Y", source=self.dataSource)
        self.magPlot.line(x=DATA.TIME, y=DATA.MAGZ, color="green", legend_label="Z", source=self.dataSource)
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
        # print("Checking for data")
        noData = False
        while not noData:
            try:
                data = self.dataQue_.get(False)
            except queue.Empty:
                noData = True
                # print("Got no data")
            else:
                print(data)


p = PayloadUI()
