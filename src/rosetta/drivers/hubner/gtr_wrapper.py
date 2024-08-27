"""
Wrapper driver for bypassing certain deficiencies of rpyc.

Primarily wraps the setter functions of rosetta.drivers.hubner.gtr

Chloe Washabaugh August 2024
"""

#from rosetta.drivers.hubner.gtr import Gtr
try:
    from rosetta.drivers.hubner import gtr
except ModuleNotFoundError:
    from drivers.hubner import gtr

class Gtr_wrapper(gtr.Gtr):
    #def get_cwave(self):
    #    return self.cwave
    
    def scan_OPO_piezo(self, min_piezo, max_piezo, scan_rate):
        
        channel = gtr.PiezoChannel.Opo
        settings = gtr.PiezoScanSettings(min_piezo,max_piezo, scan_rate)
        mode = gtr.PiezoMode.Scan

        self.set_piezo_scan_settings(channel, settings)
        self.set_piezo_mode(channel, mode)

    def stop_OPO_piezo(self, piezo = 50.0):
        channel = gtr.PiezoChannel.Opo
        mode = gtr.PiezoMode.Manual

        self.set_piezo_mode(channel, mode)
        self.set_piezo_manual_output(channel, piezo)
