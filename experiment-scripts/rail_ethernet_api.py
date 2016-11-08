import time
import socket
import sys
import string
import os
import numpy as np
from tables import *

ARDUINO_INSTRUCTIONS = {'Move' : '0', 'Calibrate' : '1',
                        'ToTheStart' : '2', 'Stop' : '3'}

HOST = '10.10.40.245'
PORT = 12345
BUFFER_LENGTH = 10000

class SLPClient():
    def __init__(self, host = None, port = None):
        if host is None:
            host = HOST
        if port is None:
            port = PORT
        self.host = host
        self.port = port

    def connect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.s.connect((self.host, self.port))
        except socket.error:
                self.s.close()
                self.s = None

        if self.s is None:
            print 'Could not open socket'
        else:
            print 'Socket opened'

    def send(self, data):
        self.error = 0

        try:
            self.s.send(data)
        except socket.error:
            self.error = -1

        if self.error < 0:
            print 'Could not send data'
        else:
            print 'Data sent: %s\n' % data

    def recv(self):
        self.data = ''
        aux = ''
        flag = False
        x = ''

        while 1:
            aux = self.s.recv(1)
            if aux:
                for x in aux:
                    self.data += x
                    if x == '\n':
                        flag = True
            else:
                break

            if flag:
                break
        return  self.data

    def send_move(self, steps, direction = None):
        if 0 < steps < (1450 * 20000 / 66.0):
            steps = steps
        else:
            print 'Number of steps out of range (0 - 439 393)'
            return

        if direction is None:
            direction = 'R'
        else:
            direction = direction

        self.steps = steps
        self.direction = direction
        self.send(data = ARDUINO_INSTRUCTIONS['Move'] + str(self.steps) + self.direction + '\n')
        print self.recv()

    def send_stop(self):
        self.send(data = ARDUINO_INSTRUCTIONS['Stop'] + '\n')

    def send_calibrate(self):
        self.send(data = ARDUINO_INSTRUCTIONS['Calibrate'] + '\n')
        print self.recv()

    def send_to_start(self):
        self.send(data = ARDUINO_INSTRUCTIONS['ToTheStart'] + '\n')
        print self.recv()

    def close(self):
        self.s.close()
        print 'Socket closed'
