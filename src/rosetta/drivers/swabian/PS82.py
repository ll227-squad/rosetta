'''
    Driver for a Swabian PulseStreamer 8/2
    D.Mark - Jun 2023
    Added additional base capabilities as listed in the API documentation (see below). Use as you wish, be chaotic.

    C.Egerstrom - Mar 2023
    De-lantz-ed version of Nazar's old driver. Use as you wish, be evil.

    N.Delegan - Sep 2020.
    Use as you wish, be nice.

    :to-do:
    De-jank init so multiple PSs doesn't break it

    leans heavily into API info at https://www.swabianinstruments.com/static/documentation/PulseStreamer/sections/api-doc.html
'''
import logging
import time
from pulsestreamer import PulseStreamer
from rpyc.utils.classic import obtain # to deal with inevitable NetRef issues

logger = logging.getLogger(__name__)

class PS82Instrument:
    """Driver for a Swabian Pulse Streamer 8/2"""

    def __init__(self, address="192.168.1.105"):

        self.address = address 
        #self.voltage_sp_ch0 = 0

    def __enter__(self):
        self.open()
        print("Swabian 8/2 Connected")
        return(self)
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def open(self):
        try:
            self.ps = PulseStreamer(self.address)
        except Exception as err:
            raise ConnectionError(f'Failed connecting to Swabian 8/2 Pulse Streamer @ [{self.address}]') from err

        #self.idn = self.device.query('*IDN?')
        #self.idn_sensor = self.device.query('SYST:SENS:IDN?')
        #self.correction_wavelength = self.device.query('SENS:CORR:WAV?')

        logger.info(f'Connected to Swabian 8/2 Pulse Streamer [{self}].')
        
        return self
    
    def close(self):
        self.ps.reset()

    ###############################################################################################################
    ############################################### Methods #######################################################
    
    def idn(self):
        '''Get device info from findPulseStreamers()'s return'''
        ser_num = self.ps.getSerial()
        frm_ver = self.ps.getFirmwareVersion()
        return "Serial #: " + ser_num + " // Firmware: " + frm_ver
    
    def reset(self):
        '''(In-built) Reset the Pulse Streamer device to the default state. 
        All outputs are set to 0V, and all functional configurations 
        are set to default. The automatic rearm functionality is enabled, 
        and the clock source is the internal clock of the device. 
        No specific trigger functionality is enabled, which means that 
        each sequence is streamed immediately when its upload is completed.'''
        self.ps.reset()

    def reset_streamer(self):
        '''Sets all digital and analog outputs to 0V'''
        self.ps.constant() # Calling the method without a parameter will result in the default output state with all output set to 0V.

    def reboot(self):
        '''(In-built) Perform a soft reboot of the device without power-cycling.'''
        self.ps.reboot()

    def streaming_state(self, verbose=False):
        '''Get streaming status status
        Arguments:  
            *verbose (bool): Default: True
        Returns:    *[If PS has a sequence, if it's streaming, if it's finishsed] 
                     as booleans if not Verbose, otherwise those are all in a string'''
        bool_seq = self.ps.hasSequence()
        bool_strm = self.ps.isStreaming()
        bool_fin = self.ps.hasFinished()
        if verbose:
            return('Sequence in memory: '+str(bool_seq)+' | Is streaming: '+str(bool_strm)\
                +' | Is finished: '+str(bool_fin))
        return([bool_seq, bool_strm, bool_fin]) #if not verbose
    
    # Run a test sequence with this method

    def test_sequence(self): #, unconnected=[0,5,6,7,'A1','A2']):
        """This is to run a test sequence that aims to test all of the channels. 
        i.e. infinite loop of 1 second TTL pulses on each of the counter channels.
        """

        # in ns
        TTL_ch0 = [(1e9,0),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1)]
        TTL_ch1 = [(1e9,1),(1e9,0),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1)]
        TTL_ch2 = [(1e9,1),(1e9,1),(1e9,0),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1)]
        TTL_ch3 = [(1e9,1),(1e9,1),(1e9,1),(1e9,0),(1e9,1),(1e9,1),(1e9,1),(1e9,1)]
        TTL_ch4 = [(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,0),(1e9,1),(1e9,1),(1e9,1)]
        TTL_ch5 = [(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,0),(1e9,1),(1e9,1)]
        TTL_ch6 = [(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,0),(1e9,1)]
        TTL_ch7 = [(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,1),(1e9,0)]
        ANG_ch0 = [(1e9,0),(1e9,0.5),(1e9,1),(1e9,-1),(1e9,-0.75),(1e9,-0.5),(1e9,-0.25),(1e9,0)]
        ANG_ch1 = [(1e9,0),(1e9,-0.5),(1e9,-1),(1e9,1),(1e9,0.75),(1e9,0.5),(1e9,0.25),(1e9,0)]

        test_sequence = self.ps.createSequence() #create the sequence class
        test_sequence.setDigital(0,TTL_ch0)
        test_sequence.setDigital(1,TTL_ch1)
        test_sequence.setDigital(2,TTL_ch2)
        test_sequence.setDigital(3,TTL_ch3)
        test_sequence.setDigital(4,TTL_ch4)
        test_sequence.setDigital(5,TTL_ch5)
        test_sequence.setDigital(6,TTL_ch6)
        test_sequence.setDigital(7,TTL_ch7)
        test_sequence.setAnalog(0,ANG_ch0)
        test_sequence.setAnalog(1,ANG_ch1)

        #n_runs = self.ps.REPEAT_INFINITELY #inifnite number of runs
        n_runs = 2
        self.ps.stream(test_sequence, n_runs)

    # Workhorse methods

    def runSequenceInfinitely(self, seq):
        '''Main workhorse function when using Swabian through an InstrumentGateway. Obtains the desired sequence and starts streaming it'''
        self.ps.stream(obtain(seq), self.ps.REPEAT_INFINITELY)

    def stream(self, seq):
        '''Main workhorse function when using Swab thru an InstrumentGateway. Obtains the desired sequence and starts streaming it'''
        self.ps.stream(obtain(seq))

    
    ###############################################################################################################
    ###############################################################################################################
    
if __name__ == '__main__':
    with PS82Instrument() as pulse_streamer:
        print(pulse_streamer.idn())
        #pulse_streamer.reset()
        #pulse_streamer.reset_streamer()
        #pulse_streamer.reboot()
        print(pulse_streamer.streaming_state(True))
        pulse_streamer.test_sequence()
        while True:
            print(pulse_streamer.streaming_state(True))
            time.sleep(0.5)

