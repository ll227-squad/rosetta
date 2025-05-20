# -*- coding: utf-8 -*-
"""
Driver for SRS396 over IP.

Copyright (c) August 2023, D.P. Mark
All rights reserved.

Modified by C. Egerstrom Mar 2024 to inherit from general sig-gen template, return vs print values for 'get' methods

This work is licensed under the terms of the 3-Clause BSD license.
For a copy, see <https://opensource.org/licenses/BSD-3-Clause>.

"""

import socket


class SRS396():

    def __init__(self, ip="192.168.1.113", port=5025, host='127.0.0.1', serialNumber=None, sock=None):
        self.serialNumber = serialNumber
        self.ip = ip
        self.port = port
        self.host = host
        self.modelnumber = None
        self.sock = sock
     
    def __enter__(self):
        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = self.sock
        self.sock.connect(("192.168.1.113", 5025))
        print(f'Connection established.' )
        return(self)

    def __exit__(self, *args):
        self.sock.close()
    
    def read(self, dtypeMethod=str):
        '''
        Read function for commands where you are expecting return values.
        Arguments:  *dtypeMethod=str: method to be used on (sanitized) data before returning
        '''
        data = self.sock.recv(1024)
        data = str(data) #just to make things easier to work with
        #print ('<SRS> ', data) #debug

        if data[:2] == "b'": #cleaning up the output
            data = data[2:-1]
        if data[0] == ";":
            data = data[1:]
        return(dtypeMethod(data))

    def start(self):
        self.sock.send(b'TYPE AM')
        self.sock.send(b'SOURCE EXT')
        self.sock.send(b'ENABLE ON')

    def idn(self):
        self.sock.send(b'*IDN?;')
        return(self.read(str).split(','))
    
    #General methods for convenience
    def getPwrLvl(self):
        return(self.rfAmp())

    def setPwrLvl(self, val):
        self.setRfAmp(val)

    def getIfRfOut(self):
        return(self.rfToggle())

    def setIfRFOut(self, val):
        self.setRfToggle(val)
    
    #general methods that are already named properly
    def getFreq(self):
        self.sock.send(b'FREQ?;')
        return(self.read(float))

    def setFreq(self, value):
        val = 'FREQ{:.2f};'.format(value)
        self.sock.send(val.encode())

    #More specific methods Daniel has written
    def rfAmp(self):
        """High freq (main) amplitude"""
        self.sock.send(b'AMPR?;')
        return(self.read(float))

    def setRfAmp(self, value):
        val = 'AMPR{:.2f};'.format(value)
        self.sock.send(val.encode())

    def rfToggle(self):
        self.sock.send(b'ENBR?;')
        return(self.read())

    def setRfToggle(self, value):
        val = 'ENBR{:.0f};'.format(value)
        self.sock.send(val.encode())

    def getPhase(self):
        self.sock.send(b'PHAS?;')
        return(self.read(float))

    def setPhase(self, value):
        val = 'PHAS{:.2f};'.format(value)
        self.sock.send(val.encode())
    
    def relPhase(self):
        '''
        set carrier phase to 0 degrees
        '''
        self.sock.send(b'RPHS;')

    def calibrate(self):
        self.sock.send(b'*CAL?;')
        return(self.read())
    
    def lfAmp(self):
        '''
        low frequency amplitude (BNC output)
        '''
        self.sock.send(b'AMPL?;')
        return(self.read())  

    def setLfAmp(self, value):
        val = 'AMPR{:.2f};'.format(value)
        self.sock.send(val.encode())

    def lfToggle(self):
        self.sock.send(b'ENBL?;')
        return(self.read())

    def setLfToggle(self, value):
        val = 'ENBL{:s};'.format(value)
        self.sock.send(val.encode())

    def getLfOffset(self):
        self.sock.send(b'OFSL?;')
        return(self.read())

    def setLfOffset(self, value):
        val = 'OFSL{:.2f};'.format(value)
        self.sock.send(val.encode())

    def getMod(self):
        '''
        Retrieve current modulation state
        1 = True
        Other = False
        '''
        self.sock.send(b'MODL?;')
        return(self.read())

    def setMod(self, value):
        val = 'MODL {};'.format(value)
        self.sock.send(val.encode())

    def getModType(self):
        self.sock.send(b'TYPE?;')
        return(self.read())

    def setModType(self, value):
        val = 'TYPE {};'.format(value)
        self.sock.send(val.encode())

    def getModFunc(self):
        self.sock.send(b'MFNC?;')
        return(self.read())

    def setModFunc(self, value):
        val = 'MFNC {};'.format(value)
        self.sock.send(val.encode())

    def getModRate(self):
        self.sock.send(b'RATE?;')
        return(self.read())

    def setModRate(self, value):
        val = 'RATE {};'.format(value)
        self.sock.send(val.encode())

    def getAmModDepth(self):
        self.sock.send(b'ADEP?;')
        return(self.read())

    def setAmModDepth(self, value):
        val = 'ADEP {};'.format(value)
        self.sock.send(val.encode())

    def getFmModDev(self):
        self.sock.send(b'FDEV?')
        return(self.read())

    def setFmModDev(self, value):
        val = 'FDEV {};'.format(value)
        self.sock.send(val.encode())

if __name__ =='__main__':
    with SRS396() as mySRS:
        print('Hi')
        print("SRS Identity:", mySRS.idn())
        print("SRS Freq", mySRS.getFreq())
        print("SRS Amp", mySRS.rfAmp())
        print("SRS Phase", mySRS.getPhase())
        print("SRS Outputting?", mySRS.rfToggle())
        

    