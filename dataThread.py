import logging
import threading
from queue import Queue
import queue
import serial
import serial.tools.list_ports
import numpy as np


class DataReceiver(threading.Thread):
    """ Class runs a thread that consistently checks serial port for data"""

    def __init__(self, serialHandler, que, *args, **kwargs):
        super(DataReceiver, self).__init__()

        # Class instance of the serial handler
        self.serialHandler_ = serialHandler

        # Que for sending out data
        self.dataQue_ = que

        # Flag that indicates whether thread should be killed
        self.kill_ = False
        self.dameon = True

        # Lists for storing data
        self.time = [0] * 10
        self.accelX = [0] * 10
        self.accelY = [0] * 10
        self.accelZ = [0] * 10
        self.gyroX = [0] * 10
        self.gyroY = [0] * 10
        self.gyroZ = [0] * 10
        self.magX = [0] * 10
        self.magY = [0] * 10
        self.magZ = [0] * 10
        self._index = 0

    def kill(self) -> None:
        self.kill_ = True

    def run(self):
        """ Consistently loops through checking serial connection for new data"""

        while not self.kill_:

            try:
                # Check serial port for new data
                msg = self.serialHandler_.readline()

            except serial.SerialException:
                # Except the condition of the serial port timing out (No data)
                pass

            else:
                data = str(msg).strip("b'").rstrip("'").rstrip("\\r\\n").split(",")

                if len(data) == 10:
                    try:
                        self.time[self._index] = float(data[0])
                        self.accelX[self._index] = float(data[1])
                        self.accelY[self._index] = float(data[2])
                        self.accelZ[self._index] = float(data[3])
                        self.gyroX[self._index] = float(data[4])
                        self.gyroY[self._index] = float(data[5])
                        self.gyroZ[self._index] = float(data[6])
                        self.magX[self._index] = float(data[7])
                        self.magY[self._index] = float(data[8])
                        self.magZ[self._index] = float(data[9])

                        self._index += 1

                        if self._index >= 10:
                            if self.dataQue_.full():
                                self.dataQue_.queue.clear()
                                print("Clearing Queue")
                            print("Put data in queue")
                            self.dataQue_.put((self.time, self.accelX, self.accelY, self.accelZ, self.gyroX, self.gyroY, self.gyroZ, self.magX, self.magY, self.magZ,))
                            self._index = 0

                    except ValueError as err:
                        print("Corrupt Data Received, Data Ignored! Data [{}]".format(data))

