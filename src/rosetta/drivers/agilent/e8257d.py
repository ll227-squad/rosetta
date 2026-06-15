"""
Driver for Agilent E8257D (20GHz sig gen)

Chloe Washabaugh, 2025
"""

import logging
from pyvisa import ResourceManager

logger = logging.getLogger(__name__)

# Show additional print statements for setters if True
output = True

class E8257DInstrument:
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
            raise ConnectionError(f'Failed connecting to E8257D @ [{self.address}]') from err
        
        # 2 second timeout
        self.device.timeout = 2000

        self.idn = self.device.query('*IDN?')

        logger.info(f'Connected to E8257D [{self}].')
        
        return self
    
    def close(self):
        self.device.close()

    #####################################################################################################
    #################################### GETTERS ########################################################
    #####################################################################################################

    def get_idn(self):
        return self.device.query('*IDN?').strip()
    
    def get_rf_toggle(self):
        return self.device.query('OUTP:STAT?')
    
    def get_rf_amp(self):
        return self.device.query('POW:AMPL?')
    
    #####################################################################################################
    #################################### SETTERS ########################################################
    #####################################################################################################

    def set_rf_toggle(self, value):
        # value = 0 (off) or 1 (on)
        self.device.write('OUTP:STAT {}'.format(value))

    def set_rf_amp(self, value):
        #dBm
        self.device.write('POW:AMPL {:.2f}'.format(value))

    def set_rf_freq(self, value):
        #Hz
        self.device.write('FREQ {:.2f}'.format(value))

    
if __name__ == '__main__':
    sig_gen = E8257DInstrument('GPIB0::2::INSTR')
    sig_gen.open()