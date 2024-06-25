"""
Driver for ThorLabs PM100USB (USB powermeter)

Chloe Washabaugh, 2024
"""

import logging
from pyvisa import ResourceManager

logger = logging.getLogger(__name__)

# Show additional print statements for setters if True
output = True

class PM100USBInstrument:
    def __init__(self, address):
        """
        Args:
            address (str): PyVISA resource path
        """
        self.rm = ResourceManager()
        self.address = address

    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self):
        self.close()
    
    def __str__(self):
        return f'{self.address} {self.idn}'
    
    def open(self):
        try:
            self.device = self.rm.open_resource(self.address)
        except Exception as err:
            raise ConnectionError(f'Failed connecting to PM100USB @ [{self.address}]') from err
        
        # 2 second timeout
        self.device.timeout = 2000

        self.idn = self.device.query('*IDN?')
        self.idn_sensor = self.device.query('SYST:SENS:IDN?')
        self.correction_wavelength = self.device.query('SENS:CORR:WAV?')

        logger.info(f'Connected to PM100USB [{self}].')
        
        return self
    
    def close(self):
        self.device.close()

    #####################################################################################################
    #################################### GETTERS ########################################################

    def get_idn(self):
        return self.device.query('*IDN?').strip()
    
    def get_idn_sensor(self):
        info = self.device.query('SYST:SENS:IDN?').split(',')
        return f'Sensor Model #: {info[0]}; Sensor Serial #: {info[1]}; Sensor last calibrated {info[2]}'
    
    def get_correction_wavelength(self):
        return float(self.device.query('SENS:CORR:WAV?'))

    def get_power(self):
        return float(self.device.query('MEAS:POWER?'))
    
    def get_units(self):
        return self.device.query('POW:UNIT?').strip()
    
    #################################### SETTERS ########################################################

    def set_correction_wavlength(self, wavelength):
        """
        Args:
                wavelength (float): correction wavlength of power meter
        """
        self.device.write('SENSE:CORRECTION:WAVELENGTH {}'.format(wavelength))
        if output == True:
            print(f'Correction wavelength set to {self.get_correction_wavelength()}nm.')

    def set_units(self,unit):
        """
        Args:
                unit (str): "W" or "DBM"
        """
        self.device.write('POW:UNIT {}'.format(unit))
        if output == True:
            print(f'Correction wavelength set to {self.get_units()}.')

    #####################################################################################################
    #####################################################################################################
    
if __name__ == '__main__':
    dev = PM100USBInstrument('USB0::0x1313::0x8072::1916964::INSTR')
    dev.open()
    print(f'-- Device identification: {dev.get_idn()}')
    print(f'-- Sensor identification: {dev.get_idn_sensor()}')
    print(f'-- Correction wavelength: {dev.get_correction_wavelength()}nm')
    print(f'-- Current power: {dev.get_power()}{dev.get_units()}')
    dev.set_correction_wavlength(675.0)
    dev.set_units('W')