import time
import logging
from pathlib import Path
from itertools import count
import numpy as np
from nspyre import nspyre_init_logger
from nspyre import StreamingList, DataSource, experiment_widget_process_queue

from rosetta.insmgr import MyInstrumentManager
from rpyc.utils.classic import obtain

from rosetta.drivers.ni.ni_analogTasks import nidaqAnalogTasks

_HERE = Path(__file__).parent
_logger = logging.getLogger(__name__)

class mwPowerExperiment:
    " Monitor power of Schottkey diode on analog input of DAQ, task vs time style."
    def __init__(self, queue_to_exp=None, queue_from_exp=None):
        """
        Args:
            queue_to_exp: A multiprocessing Queue object used to send messages
                to the experiment from the GUI.
            queue_from_exp: A multiprocessing Queue object used to send 
                messages to the GUI from the experiment.
        """
        self.queue_to_exp = queue_to_exp
        self.queue_from_exp = queue_from_exp

    def __enter__(self):
        """Perform experiment setup."""
        # config logging messages
        # if running a method from the GUI, it will be run in a new process
        # this logging call is necessary in order to separate log messages
        # originating in the GUI from those in the new experiment subprocess
        nspyre_init_logger(
            log_level=logging.INFO,
            log_path=_HERE / '../logs',
            log_path_level=logging.DEBUG,
            prefix=Path(__file__).stem,
            file_size=10_000_000,
        )
        _logger.info('Created mwPowerExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed mwPowerExperiment instance.')

    def mwPowerTrace(self,
                    rate,
                    num_points,
                    AI_channel:str,
                    dataset:str):
        "AI channel must include Dev1 pointer, e.g. Dev1/AI0"
        with MyInstrumentManager() as mgr, DataSource(dataset) as mwPower_data:
            mwPower_driver = mgr.ni_analogTasks

            self.times = StreamingList()
            self.powers = StreamingList()

            self.startTime = time.time()

            # get number of times to sample power meter
            if num_points < 0:
                num_samples = count() # infinite iterator
            else:
                num_samples = range(int(num_points))

            # main experiment loop
            for i in num_samples:
                current_time = time.time()-self.startTime
                current_power = mwPower_driver.readAI(AI_channel)
                
                self.times.append(current_time)
                self.powers.append(current_power*1000)
                time.sleep(1/rate)


                # save the current data to the data server
                mwPower_data.push({'params':{'rate':rate,'num_points':num_points},
                                     'title': 'MW power into cryostat time trace',
                                     'xlabel': 'Time (s)',
                                     'ylabel': "Power (mV)",
                                     'units': 'mV vs s',
                                     'datasets':{'times'      : self.times,
                                                 'powers'     : self.powers}
                                     })

                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    return    
                
class cwODMRExperiment:
    " Different flavors of CW-ODMR"
    def __init__(self, queue_to_exp=None, queue_from_exp=None):
        """
        Args:
            queue_to_exp: A multiprocessing Queue object used to send messages
                to the experiment from the GUI.
            queue_from_exp: A multiprocessing Queue object used to send 
                messages to the GUI from the experiment.
        """
        self.queue_to_exp = queue_to_exp
        self.queue_from_exp = queue_from_exp

    def __enter__(self):
        """Perform experiment setup."""
        # config logging messages
        # if running a method from the GUI, it will be run in a new process
        # this logging call is necessary in order to separate log messages
        # originating in the GUI from those in the new experiment subprocess
        nspyre_init_logger(
            log_level=logging.INFO,
            log_path=_HERE / '../logs',
            log_path_level=logging.DEBUG,
            prefix=Path(__file__).stem,
            file_size=10_000_000,
        )
        _logger.info('Created cwODMRExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed cwODMRExperiment instance.')

    def cwODMRfemtoExperiment(self,
                         dataset:str,
                         start_freq,
                         stop_freq,
                         num_points,
                         dwell_time,
                         iterations,
                         mw_power,
                         femto_channel,
                         schottky_channel):
        """
        start_freq in MHz
        stop_freq in MHz
        num_points in each frequency sweep
        dwell_time in ms for each frequency (and for each background point)
        iterations--number of frequency sweeps
        mw_power in dBm
        femto_channel is 'Dev1/AI4'
        schottky_channel is 'Dev1/AI0'
        ps_channel 
        """
        with MyInstrumentManager() as mgr, DataSource(dataset) as cwODMRfemto_data:
            # Take care of units
            start_freq = start_freq*1e6
            stop_freq  = stop_freq*1e6
            dwell_time = dwell_time*1e-3

            srs            = mgr.srs_driver
            femto          = mgr.ni_analogTasks
            schottky_diode = mgr.ni_analogTasks

            times = StreamingList()
            signal_data = StreamingList()
            background_data = StreamingList()
            schottky_data = StreamingList()

            frequencies = np.linspace(start_freq, stop_freq, num_points)

            # Set starting point of SRS396
            srs.setFreq(start_freq)
            print('Set SRS396 frequency to {freq:.6f} MHz.'.format(freq = start_freq/1e6))
            srs.setRfAmp(mw_power)
            print('Set SRS396 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
            srs.setRfToggle(1)
            print('Turn on RF output of SRS396.')

            # Iterations is number of passes over whole frequency range
            for i in range(iterations):
                # Initialize this iteration to NaN in _data StreamingLists
                signal_voltages = np.empty(num_points)
                signal_voltages[:] = np.nan
                signal_data.append(np.stack([frequencies/1e6, signal_voltages]))
                background_voltages = np.empty(num_points)
                background_voltages[:] = np.nan
                background_data.append(np.stack([frequencies/1e6, background_voltages]))
                schottky_voltages = np.empty(num_points)
                schottky_voltages[:] = np.nan
                schottky_data.append(np.stack([frequencies/1e6, schottky_voltages]))

                # For each frequency in frequency range
                for f, freq in enumerate(frequencies):
                    print('Frequency: {frequency:.6f} MHz. Iteration: {iteration}.'.format(frequency = freq/1e6, iteration = i+1))
                    ### Get signal
                    srs.setRfToggle(1)
                    srs.setFreq(freq)
                    # wait half of dwell time
                    time.sleep(dwell_time/2)
                    # read power that gets put into cryostat
                    schottky_data[-1][1][f] = schottky_diode.readAI(schottky_channel)
                    # read the number of photon counts received by the photon counter.
                    signal_data[-1][1][f] = femto.readAI(femto_channel)
                    # notify the streaminglist that this entry has updated so it will be pushed to the data server
                    signal_data.updated_item(-1)
                    # wait half of dwell time
                    time.sleep(dwell_time/2)


                    ### Get background
                    srs.setRfToggle(0)
                    # wait half of dwell time
                    time.sleep(dwell_time/2)
                    # read power that gets put into cryostat
                    #schottky_data[-1][1][f] = schottky_diode.readAI(schottky_channel)
                    # read the number of photon counts received by the photon counter.
                    background_data[-1][1][f] = femto.readAI(femto_channel)
                    # notify the streaminglist that this entry has updated so it will be pushed to the data server
                    background_data.updated_item(-1)
                    # wait half of dwell time
                    time.sleep(dwell_time/2)

                    # save the current data to the data server.
                    cwODMRfemto_data.push({'params': {'start_freq_MHz': start_freq,
                                                 'stop_freq_MHz': stop_freq, 
                                                 'num_points': num_points,
                                                 'dwell_time_ms': dwell_time, 
                                                 'iterations': iterations,
                                                 'mw_power_dBm':mw_power,
                                                 'femto_channel':femto_channel,
                                                 'schottky_channel':schottky_channel},
                                    'title': 'Continuous-Wave Optically Detected Magnetic Resonance',
                                    'xlabel': 'Frequency (MHz)',
                                    'ylabel': 'Femto Voltage (mV)',
                                    'datasets': {'signal' : signal_data,
                                                'background': background_data,
                                                'schottky': schottky_data}
                    })
                    if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                        # the GUI has asked us nicely to exit
                        return

            srs.setRfToggle(0)
            srs.setFreq(start_freq)
            print('Done with cwODMRfemtoExperiment.')

    def cwODMRsnspdExperiment(self,
                         dataset:str,
                         start_freq,
                         stop_freq,
                         num_points,
                         iterations,
                         laser_wavelength,
                         laser_power,
                         mw_power,
                         readout_delay,
                         acq_rate,
                         num_samples,
                         record_power,
                         SNSPD_channel,
                         PS_channel,
                         schottky_channel,
                         ps_channel_EN,
                         ps_channel_CTRL,
                         ps_channel_DAQ,
                         ps_channel_AOM,
                         ps_aomAnalog_channel,
                         comments):
        """
        start_freq in MHz
        stop_freq in MHz
        num_points in each frequency sweep
        sweep_rate in Hz, dwell time at each frequency
        iterations--number of frequency sweeps
        mw_power in dBm
        readout_delay in ms is the time between when the rf is switched on/off and when countings begins
        acq_rate in Hz, rate at which to sample SNSPD counts (integration bin)
        num_samples, number of samples to read at each point (signal or background); acq_rate/num_samples >= sweep_rate/2
        SNSPD_channel is '/Dev1/PFI1'
        PS_channel is '/Dev1/PFI2'
        schottky_channel is '/Dev1/AI0' (need slash)
        ps_channel_EN is '0'
        ps_channel_CTRL is '1'
        ps_channel_DAQ is '2' (copy of channel 1)
        """
        with MyInstrumentManager() as mgr, DataSource(dataset) as cwODMRsnspd_data:
            # Take care of units
            start_freq = start_freq*1e6 #Hz
            stop_freq  = stop_freq*1e6 #Hz
            readout_delay = readout_delay*1e-3 #s

            #process inputs
            snspd_ch = [int(SNSPD_channel[-1])]

            srs            = mgr.srs_driver
            snspd          = mgr.ni_photonCounting
            schottky_diode = mgr.ni_analogTasks
            pulsestreamer  = mgr.pulseStreamer_driver
            if record_power==True:
                pm  = mgr.powerMeter_driver
                pm.set_correction_wavelength(laser_wavelength) # send as nm
                calibration_wavelength = pm.get_correction_wavelength()
            else:
                calibration_wavelength = None

            times = StreamingList()
            signal_data = StreamingList()
            background_data = StreamingList()
            schottky_data = StreamingList()
            power_data = StreamingList()

            frequencies = np.linspace(start_freq, stop_freq, num_points)

            # Set starting point of SRS396
            srs.setFreq(start_freq)
            print('Set SRS396 frequency to {freq:.6f} MHz.'.format(freq = start_freq/1e6))
            srs.setRfAmp(mw_power)
            print('Set SRS396 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
            srs.setRfToggle(1)
            print('Turn on RF output of SRS396.')

            # Set up pulse streamer
            #d = 1/sweep_rate/2*(10**9) #ns
            #r = readout_delay
            #do0 = [(r,0),(d/2,0),(d/2-r,0),(r,0),(d/2,0),(d/2-r,0)] # EN input of switch
            #do1 = [(r,1),(d/2,1),(d/2-r,1),(r,0),(d/2,0),(d/2-r,0)] # CTRL input of switch
            #do2 = [(r,0),(d/2,1),(d/2-r,0),(r,0),(d/2,1),(d/2-r,0)] # to PFI2 of DAQ to trigger counter acquisition

            #cwODMRsequence = pulsestreamer.ps.createSequence()
            #cwODMRsequence.setDigital(ps_channel_EN,do0)
            #cwODMRsequence.setDigital(ps_channel_CTRL,do1)
            #cwODMRsequence.setDigital(ps_channel_DAQ,do2)

            #pulsestreamer.runSequenceInfinitely(cwODMRsequence)

            mwON = pulsestreamer.ps.createSequence()
            mwON.setDigital(ps_channel_EN, [(num_samples/acq_rate*1e9,0)])
            mwON.setDigital(ps_channel_CTRL, [(num_samples/acq_rate*1e9,1)])
            mwON.setDigital(ps_channel_DAQ, [(num_samples/acq_rate*1e9,1)])
            mwON.setDigital(ps_channel_AOM, [(num_samples/acq_rate*1e9,1)])
            mwON.setAnalog(ps_aomAnalog_channel, [(num_samples/acq_rate*1e9,1.0)])

            mwOFF = pulsestreamer.ps.createSequence()
            mwOFF.setDigital(ps_channel_EN, [(num_samples/acq_rate*1e9,0)])
            mwOFF.setDigital(ps_channel_CTRL, [(num_samples/acq_rate*1e9,0)])
            mwOFF.setDigital(ps_channel_DAQ, [(num_samples/acq_rate*1e9,1)])
            mwOFF.setDigital(ps_channel_AOM, [(num_samples/acq_rate*1e9,1)])
            mwOFF.setAnalog(ps_aomAnalog_channel, [(num_samples/acq_rate*1e9,1.0)])

            # Iterations is number of passes over whole frequency range
            for i in range(iterations):
                # Initialize this iteration to NaN in _data StreamingLists
                signal_voltages = np.empty(num_points)
                signal_voltages[:] = np.nan
                signal_data.append(np.stack([frequencies/1e6, signal_voltages]))
                background_voltages = np.empty(num_points)
                background_voltages[:] = np.nan
                background_data.append(np.stack([frequencies/1e6, background_voltages]))
                schottky_voltages = np.empty(num_points)
                schottky_voltages[:] = np.nan
                schottky_data.append(np.stack([frequencies/1e6, schottky_voltages]))
                power_empty = np.empty(num_points)
                power_empty[:] = np.nan
                power_data.append(np.stack([frequencies/1e6, power_empty]))

                # For each frequency in frequency range
                for f, freq in enumerate(frequencies):
                    print('Frequency: {frequency:.6f} MHz. Iteration: {iteration}.'.format(frequency = freq/1e6, iteration = i+1))
                    ### Get signal ###
                    pulsestreamer.runSequenceInfinitely(mwON)
                    time.sleep(readout_delay)
                    srs.setFreq(freq)
                    # read power that gets put into cryostat
                    schottky_data[-1][1][f] = 0#schottky_diode.readAI(schottky_channel)
                    # read the number of photon counts received by the photon counter.
                    start_time = time.time()

                    if record_power==True:
                        current_optical_power = pm.get_power() * 1e3 #mW
                    else:
                        current_optical_power = 1.0

                    signal = np.average(snspd.readCtrs_multi_internalClk(acq_rate, num_samples,snspd_ch))
                    signal_data[-1][1][f] = signal
                    end_time = time.time()-start_time
                    # notify the streaminglist that this entry has updated so it will be pushed to the data server
                    signal_data.updated_item(-1)

                    ### Get background ###
                    # read the number of photon counts received by the photon counter.
                    pulsestreamer.runSequenceInfinitely(mwOFF)
                    time.sleep(readout_delay)
                    background = np.average(snspd.readCtrs_multi_internalClk(acq_rate, num_samples,snspd_ch))
                    background_data[-1][1][f] = background
                    # notify the streaminglist that this entry has updated so it will be pushed to the data server
                    background_data.updated_item(-1)

                    power_data[-1][1][f] = current_optical_power #mW
                    power_data.updated_item(-1)

                    # save the current data to the data server.
                    cwODMRsnspd_data.push({'params': {'start_freq_MHz': start_freq/1e6,
                                                 'stop_freq_MHz': stop_freq/1e6, 
                                                 'num_points': num_points,
                                                 'iterations': iterations,
                                                 'laser_wavelength_nm':laser_wavelength,
                                                 'laser_power_mW':laser_power,
                                                 'mw_power_dBm':mw_power,
                                                 'readout_delay_ms': readout_delay*1e3,
                                                 'acq_rate' : acq_rate,
                                                 'num_samples' :num_samples,
                                                 'record_power'   : record_power,
                                                 'SNSPD_channel': SNSPD_channel,
                                                 'PS_channel': PS_channel,
                                                 'schottky_channel':schottky_channel,
                                                 'ps_channel_EN' : ps_channel_EN,
                                                 'ps_channel_CTRL': ps_channel_CTRL,
                                                 'ps_channel_DAQtrigger': ps_channel_DAQ,
                                                 'ps_channel_AOM': ps_channel_AOM,
                                                 'ps_channel_AOManalog': ps_aomAnalog_channel,
                                                 'comments': comments},
                                    'title': 'Continuous-Wave Optically Detected Magnetic Resonance',
                                    'xlabel': 'Frequency (MHz)',
                                    'ylabel': 'Counts per {t:.3}s'.format(t=1/acq_rate),
                                    'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                    'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                    'datasets': {'signal' : signal_data,
                                                'background': background_data,
                                                'schottky': schottky_data,
                                                'power'  : power_data,}
                    })
                    if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                        # the GUI has asked us nicely to exit
                        return

            srs.setRfToggle(0)
            srs.setFreq(start_freq)
            print('Done with cwODMRsnspdExperiment.')

    def cwODMRsnspdE8257DExperiment(self,
                            dataset:str,
                            start_freq,
                            stop_freq,
                            num_points,
                            iterations,
                            laser_wavelength,
                            laser_power,
                            mw_power,
                            readout_delay,
                            acq_rate,
                            num_samples,
                            record_power,
                            SNSPD_channel,
                            PS_channel,
                            schottky_channel,
                            ps_channel_EN,
                            ps_channel_CTRL,
                            ps_channel_DAQ,
                            ps_channel_AOM,
                            ps_aomAnalog_channel,
                            comments):
            """
            start_freq in MHz
            stop_freq in MHz
            num_points in each frequency sweep
            sweep_rate in Hz, dwell time at each frequency
            iterations--number of frequency sweeps
            mw_power in dBm
            readout_delay in ms is the time between when the rf is switched on/off and when countings begins
            acq_rate in Hz, rate at which to sample SNSPD counts (integration bin)
            num_samples, number of samples to read at each point (signal or background); acq_rate/num_samples >= sweep_rate/2
            SNSPD_channel is '/Dev1/PFI1'
            PS_channel is '/Dev1/PFI2'
            schottky_channel is '/Dev1/AI0' (need slash)
            ps_channel_EN is '0'
            ps_channel_CTRL is '1'
            ps_channel_DAQ is '2' (copy of channel 1)
            """
            with MyInstrumentManager() as mgr, DataSource(dataset) as cwODMRsnspdE8257D_data:
                # Take care of units
                start_freq = start_freq*1e6 #Hz
                stop_freq  = stop_freq*1e6 #Hz
                readout_delay = readout_delay*1e-3 #s

                #process inputs
                snspd_ch = [int(SNSPD_channel[-1])]

                agilent        = mgr.e8257d_driver2 #MW sig gen
                snspd          = mgr.ni_photonCounting
                schottky_diode = mgr.ni_analogTasks
                pulsestreamer  = mgr.pulseStreamer_driver
                if record_power==True:
                    pm  = mgr.powerMeter_driver
                    pm.set_correction_wavelength(laser_wavelength) # send as nm
                    calibration_wavelength = pm.get_correction_wavelength()
                else:
                    calibration_wavelength = None

                times = StreamingList()
                signal_data = StreamingList()
                background_data = StreamingList()
                schottky_data = StreamingList()
                power_data = StreamingList()

                frequencies = np.linspace(start_freq, stop_freq, num_points)

                # Set starting point of SRS396
                agilent.set_rf_freq(start_freq)
                print('Set SRS396 frequency to {freq:.6f} MHz.'.format(freq = start_freq/1e6))
                agilent.set_rf_amp(mw_power)
                print('Set SRS396 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
                agilent.set_rf_toggle(1)
                print('Turn on RF output of SRS396.')

                # Set up pulse streamer
                #d = 1/sweep_rate/2*(10**9) #ns
                #r = readout_delay
                #do0 = [(r,0),(d/2,0),(d/2-r,0),(r,0),(d/2,0),(d/2-r,0)] # EN input of switch
                #do1 = [(r,1),(d/2,1),(d/2-r,1),(r,0),(d/2,0),(d/2-r,0)] # CTRL input of switch
                #do2 = [(r,0),(d/2,1),(d/2-r,0),(r,0),(d/2,1),(d/2-r,0)] # to PFI2 of DAQ to trigger counter acquisition

                #cwODMRsequence = pulsestreamer.ps.createSequence()
                #cwODMRsequence.setDigital(ps_channel_EN,do0)
                #cwODMRsequence.setDigital(ps_channel_CTRL,do1)
                #cwODMRsequence.setDigital(ps_channel_DAQ,do2)

                #pulsestreamer.runSequenceInfinitely(cwODMRsequence)

                mwON = pulsestreamer.ps.createSequence()
                mwON.setDigital(ps_channel_EN, [(num_samples/acq_rate*1e9,0)])
                mwON.setDigital(ps_channel_CTRL, [(num_samples/acq_rate*1e9,1)])
                mwON.setDigital(ps_channel_DAQ, [(num_samples/acq_rate*1e9,1)])
                mwON.setDigital(ps_channel_AOM, [(num_samples/acq_rate*1e9,1)])
                mwON.setAnalog(ps_aomAnalog_channel, [(num_samples/acq_rate*1e9,laser_power)])

                mwOFF = pulsestreamer.ps.createSequence()
                mwOFF.setDigital(ps_channel_EN, [(num_samples/acq_rate*1e9,0)])
                mwOFF.setDigital(ps_channel_CTRL, [(num_samples/acq_rate*1e9,0)])
                mwOFF.setDigital(ps_channel_DAQ, [(num_samples/acq_rate*1e9,1)])
                mwOFF.setDigital(ps_channel_AOM, [(num_samples/acq_rate*1e9,1)])
                mwOFF.setAnalog(ps_aomAnalog_channel, [(num_samples/acq_rate*1e9,laser_power)])

                # Iterations is number of passes over whole frequency range
                for i in range(iterations):
                    # Initialize this iteration to NaN in _data StreamingLists
                    signal_voltages = np.empty(num_points)
                    signal_voltages[:] = np.nan
                    signal_data.append(np.stack([frequencies/1e6, signal_voltages]))
                    background_voltages = np.empty(num_points)
                    background_voltages[:] = np.nan
                    background_data.append(np.stack([frequencies/1e6, background_voltages]))
                    schottky_voltages = np.empty(num_points)
                    schottky_voltages[:] = np.nan
                    schottky_data.append(np.stack([frequencies/1e6, schottky_voltages]))
                    power_empty = np.empty(num_points)
                    power_empty[:] = np.nan
                    power_data.append(np.stack([frequencies/1e6, power_empty]))

                    # For each frequency in frequency range
                    for f, freq in enumerate(frequencies):
                        print('Frequency: {frequency:.6f} MHz. Iteration: {iteration}.'.format(frequency = freq/1e6, iteration = i+1))
                        ### Get signal ###
                        pulsestreamer.runSequenceInfinitely(mwON)
                        agilent.set_rf_freq(freq)
                        time.sleep(readout_delay)
                        # read power that gets put into cryostat
                        schottky_data[-1][1][f] = 0#schottky_diode.readAI(schottky_channel)
                        # read the number of photon counts received by the photon counter.
                        start_time = time.time()

                        if record_power==True:
                            current_optical_power = pm.get_power() * 1e3 #mW
                        else:
                            current_optical_power = 1.0

                        signal = np.average(snspd.readCtrs_multi_internalClk(acq_rate, num_samples,snspd_ch))
                        signal_data[-1][1][f] = signal
                        end_time = time.time()-start_time
                        # notify the streaminglist that this entry has updated so it will be pushed to the data server
                        signal_data.updated_item(-1)

                        ### Get background ###
                        # read the number of photon counts received by the photon counter.
                        pulsestreamer.runSequenceInfinitely(mwON)
                        agilent.set_rf_freq(start_freq)
                        time.sleep(readout_delay)
                        background = np.average(snspd.readCtrs_multi_internalClk(acq_rate, num_samples,snspd_ch))
                        background_data[-1][1][f] = background
                        # notify the streaminglist that this entry has updated so it will be pushed to the data server
                        background_data.updated_item(-1)


                        power_data[-1][1][f] = current_optical_power #mW
                        power_data.updated_item(-1)

                        # save the current data to the data server.
                        cwODMRsnspdE8257D_data.push({'params': {'start_freq_MHz': start_freq/1e6,
                                                    'stop_freq_MHz': stop_freq/1e6, 
                                                    'num_points': num_points,
                                                    'iterations': iterations,
                                                    'laser_wavelength_nm':laser_wavelength,
                                                    'laser_power_V':laser_power,
                                                    'mw_power_dBm':mw_power,
                                                    'readout_delay_ms': readout_delay*1e3,
                                                    'acq_rate' : acq_rate,
                                                    'num_samples' :num_samples,
                                                    'record_power'   : record_power, 
                                                    'SNSPD_channel': SNSPD_channel,
                                                    'PS_channel': PS_channel,
                                                    'schottky_channel':schottky_channel,
                                                    'ps_channel_EN' : ps_channel_EN,
                                                    'ps_channel_CTRL': ps_channel_CTRL,
                                                    'ps_channel_DAQtrigger': ps_channel_DAQ,
                                                    'ps_channel_AOM': ps_channel_AOM,
                                                    'ps_channel_AOManalog': ps_aomAnalog_channel,
                                                    'comments': comments},
                                        'title': 'Continuous-Wave Optically Detected Magnetic Resonance with E8257D',
                                        'xlabel': 'Frequency (MHz)',
                                        'ylabel': 'Counts per {t:.3}s'.format(t=1/acq_rate),
                                        'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                        'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                        'datasets': {'signal' : signal_data,
                                                    'background': background_data,
                                                    'schottky': schottky_data,
                                                    'power'  : power_data,}
                        })
                        if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                            # the GUI has asked us nicely to exit
                            return
                        
                        

                agilent.set_rf_toggle(0)
                agilent.set_rf_freq(start_freq)
                print('Done with cwODMRsnspdE8257DExperiment.')

    def cwODMRsnspdE8257DdutycycleExperiment(self,
                            dataset:str,
                            start_freq,
                            stop_freq,
                            num_points,
                            iterations,
                            laser_wavelength,
                            laser_power,
                            mw_power,
                            readout_delay,
                            acq_rate,
                            num_samples,
                            duty_cycle,
                            record_power,
                            SNSPD_channel,
                            PS_channel,
                            schottky_channel,
                            ps_channel_EN,
                            ps_channel_CTRL,
                            ps_channel_DAQ,
                            ps_channel_AOM,
                            ps_aomAnalog_channel,
                            comments):
            """
            start_freq in MHz
            stop_freq in MHz
            num_points in each frequency sweep
            sweep_rate in Hz, dwell time at each frequency
            iterations--number of frequency sweeps
            mw_power in dBm
            readout_delay in ms is the time between when the rf is switched on/off and when countings begins
            acq_rate in Hz, rate at which to sample SNSPD counts (integration bin)
            num_samples, number of samples to read at each point (signal or background); acq_rate/num_samples >= sweep_rate/2
            SNSPD_channel is '/Dev1/PFI1'
            PS_channel is '/Dev1/PFI2'
            schottky_channel is '/Dev1/AI0' (need slash)
            ps_channel_EN is '0'
            ps_channel_CTRL is '1'
            ps_channel_DAQ is '2' (copy of channel 1)
            """
            with MyInstrumentManager() as mgr, DataSource(dataset) as cwODMRsnspdE8257Ddutycycle_data:
                # Take care of units
                start_freq = start_freq*1e6 #Hz
                stop_freq  = stop_freq*1e6 #Hz
                readout_delay = readout_delay*1e-3 #s
                cooling_delay = (1-2*duty_cycle)/(2*duty_cycle)*(readout_delay+num_samples/acq_rate) #s
                print(cooling_delay)

                #process inputs
                snspd_ch = [int(SNSPD_channel[-1])]

                agilent        = mgr.e8257d_driver2 #MW sig gen
                snspd          = mgr.ni_photonCounting
                schottky_diode = mgr.ni_analogTasks
                pulsestreamer  = mgr.pulseStreamer_driver
                if record_power==True:
                    pm  = mgr.powerMeter_driver
                    pm.set_correction_wavelength(laser_wavelength) # send as nm
                    calibration_wavelength = pm.get_correction_wavelength()
                else:
                    calibration_wavelength = None

                times = StreamingList()
                signal_data = StreamingList()
                background_data = StreamingList()
                schottky_data = StreamingList()
                power_data = StreamingList()

                frequencies = np.linspace(start_freq, stop_freq, num_points)
                

                # Set starting point of SRS396
                agilent.set_rf_freq(start_freq)
                print('Set SRS396 frequency to {freq:.6f} MHz.'.format(freq = start_freq/1e6))
                agilent.set_rf_amp(mw_power)
                print('Set SRS396 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
                agilent.set_rf_toggle(1)
                print('Turn on RF output of SRS396.')

                # Set up pulse streamer
                #d = 1/sweep_rate/2*(10**9) #ns
                #r = readout_delay
                #do0 = [(r,0),(d/2,0),(d/2-r,0),(r,0),(d/2,0),(d/2-r,0)] # EN input of switch
                #do1 = [(r,1),(d/2,1),(d/2-r,1),(r,0),(d/2,0),(d/2-r,0)] # CTRL input of switch
                #do2 = [(r,0),(d/2,1),(d/2-r,0),(r,0),(d/2,1),(d/2-r,0)] # to PFI2 of DAQ to trigger counter acquisition

                #cwODMRsequence = pulsestreamer.ps.createSequence()
                #cwODMRsequence.setDigital(ps_channel_EN,do0)
                #cwODMRsequence.setDigital(ps_channel_CTRL,do1)
                #cwODMRsequence.setDigital(ps_channel_DAQ,do2)

                #pulsestreamer.runSequenceInfinitely(cwODMRsequence)

                mwON = pulsestreamer.ps.createSequence()
                mwON.setDigital(ps_channel_EN, [(num_samples/acq_rate*1e9,0)])
                mwON.setDigital(ps_channel_CTRL, [(num_samples/acq_rate*1e9,1)])
                mwON.setDigital(ps_channel_DAQ, [(num_samples/acq_rate*1e9,1)])
                mwON.setDigital(ps_channel_AOM, [(num_samples/acq_rate*1e9,1)])
                mwON.setAnalog(ps_aomAnalog_channel, [(num_samples/acq_rate*1e9,1.0)])

                mwOFF = pulsestreamer.ps.createSequence()
                mwOFF.setDigital(ps_channel_EN, [(num_samples/acq_rate*1e9,0)])
                mwOFF.setDigital(ps_channel_CTRL, [(num_samples/acq_rate*1e9,0)])
                mwOFF.setDigital(ps_channel_DAQ, [(num_samples/acq_rate*1e9,1)])
                mwOFF.setDigital(ps_channel_AOM, [(num_samples/acq_rate*1e9,1)])
                mwOFF.setAnalog(ps_aomAnalog_channel, [(num_samples/acq_rate*1e9,1.0)])

                # Iterations is number of passes over whole frequency range
                for i in range(iterations):
                    # Initialize this iteration to NaN in _data StreamingLists
                    signal_voltages = np.empty(num_points)
                    signal_voltages[:] = np.nan
                    signal_data.append(np.stack([frequencies/1e6, signal_voltages]))
                    background_voltages = np.empty(num_points)
                    background_voltages[:] = np.nan
                    background_data.append(np.stack([frequencies/1e6, background_voltages]))
                    schottky_voltages = np.empty(num_points)
                    schottky_voltages[:] = np.nan
                    schottky_data.append(np.stack([frequencies/1e6, schottky_voltages]))
                    power_empty = np.empty(num_points)
                    power_empty[:] = np.nan
                    power_data.append(np.stack([frequencies/1e6, power_empty]))

                    # For each frequency in frequency range
                    for f, freq in enumerate(frequencies):
                        print('Frequency: {frequency:.6f} MHz. Iteration: {iteration}.'.format(frequency = freq/1e6, iteration = i+1))
                        ### Get signal ###
                        pulsestreamer.runSequenceInfinitely(mwON)
                        agilent.set_rf_freq(freq)
                        time.sleep(readout_delay)
                        # read power that gets put into cryostat
                        schottky_data[-1][1][f] = 0#schottky_diode.readAI(schottky_channel)
                        # read the number of photon counts received by the photon counter.
                        start_time = time.time()

                        if record_power==True:
                            current_optical_power = pm.get_power() * 1e3 #mW
                        else:
                            current_optical_power = 1.0

                        signal = np.average(snspd.readCtrs_multi_internalClk(acq_rate, num_samples,snspd_ch))
                        signal_data[-1][1][f] = signal
                        end_time = time.time()-start_time
                        # notify the streaminglist that this entry has updated so it will be pushed to the data server
                        signal_data.updated_item(-1)

                        ### Get background ###
                        # read the number of photon counts received by the photon counter.
                        pulsestreamer.runSequenceInfinitely(mwOFF)
                        time.sleep(cooling_delay)
                        time.sleep(readout_delay)
                        background = np.average(snspd.readCtrs_multi_internalClk(acq_rate, num_samples,snspd_ch))
                        background_data[-1][1][f] = background
                        # notify the streaminglist that this entry has updated so it will be pushed to the data server
                        background_data.updated_item(-1)

                        power_data[-1][1][f] = current_optical_power #mW
                        power_data.updated_item(-1)
                        
                        time.sleep(cooling_delay)

                        # save the current data to the data server.
                        cwODMRsnspdE8257Ddutycycle_data.push({'params': {'start_freq_MHz': start_freq/1e6,
                                                    'stop_freq_MHz': stop_freq/1e6, 
                                                    'num_points': num_points,
                                                    'iterations': iterations,
                                                    'laser_wavelength_nm':laser_wavelength,
                                                    'laser_power_mW':laser_power,
                                                    'mw_power_dBm':mw_power,
                                                    'readout_delay_ms': readout_delay*1e3,
                                                    'acq_rate' : acq_rate,
                                                    'num_samples' :num_samples,
                                                    'duty_cycle' : duty_cycle,
                                                    'cooling_delay_ms': cooling_delay*1e3,
                                                    'record_power'   : record_power, 
                                                    'SNSPD_channel': SNSPD_channel,
                                                    'PS_channel': PS_channel,
                                                    'schottky_channel':schottky_channel,
                                                    'ps_channel_EN' : ps_channel_EN,
                                                    'ps_channel_CTRL': ps_channel_CTRL,
                                                    'ps_channel_DAQtrigger': ps_channel_DAQ,
                                                    'ps_channel_AOM': ps_channel_AOM,
                                                    'ps_channel_AOManalog': ps_aomAnalog_channel,
                                                    'comments': comments},
                                        'title': 'Continuous-Wave Optically Detected Magnetic Resonance with E8257D, control over duty cycle',
                                        'xlabel': 'Frequency (MHz)',
                                        'ylabel': 'Counts per {t:.3}s'.format(t=1/acq_rate),
                                        'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                        'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                        'datasets': {'signal' : signal_data,
                                                    'background': background_data,
                                                    'schottky': schottky_data,
                                                    'power'  : power_data,}
                        })
                        if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                            # the GUI has asked us nicely to exit
                            return

                agilent.set_rf_toggle(0)
                agilent.set_rf_freq(start_freq)
                print('Done with cwODMRsnspdE8257DdutycycleExperiment.')

    def cwODMRsnspdE8257DfastswitchingExperiment(self,
                            dataset:str,
                            start_freq,
                            stop_freq,
                            num_points,
                            iterations,
                            laser_wavelength,
                            laser_power,
                            mw_power,
                            readout_delay,
                            cooling_delay,
                            duty_cycle,
                            dwell_rate,
                            num_samples,
                            record_power,
                            daq_cts_channel,
                            daq_trig_channel,
                            daq_clk_channel,
                            ps_EN_channel,
                            ps_CTRL_channel,
                            ps_trig_channel,
                            ps_clk_channel,
                            ps_aom_channel,
                            ps_aomAnalog_channel,
                            comments):
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as cwODMRsnspdE8257Dfastswitching_data:
                # Take care of units
                start_freq = start_freq*1e6 #Hz
                stop_freq = stop_freq*1e6   #Hz
                dwell_time = 1/dwell_rate*1e9 #ns
                cooling_time = (100/duty_cycle)*dwell_time*(1-2*(duty_cycle/100)) #ns
                print("Time per point: {tau}ms".format(tau = (dwell_time+cooling_time+dwell_time)*num_samples*1e-6))
                clk_width = dwell_time/4 #ns
                readout_delay = readout_delay/1e3 #s
                frequencies = np.linspace(start_freq, stop_freq, num_points)

                agilent2 = mgr.e8257d_driver2
                daq = mgr.ni_photonCounting
                pulsestreamer = mgr.pulseStreamer_driver

                if record_power==True:
                    pm  = mgr.powerMeter_driver
                    pm.set_correction_wavelength(laser_wavelength) # send as nm
                    calibration_wavelength = pm.get_correction_wavelength()
                else:
                    calibration_wavelength = None

                signal_data = StreamingList()
                background_data = StreamingList()
                power_data = StreamingList()

                mwOFF = pulsestreamer.cwODMRmwOFF(1e9)
                cwODMRSeq = pulsestreamer.ps.createSequence()

                if cooling_delay:
                    patt0 = [(cooling_time+dwell_time+dwell_time,0)]

                    patt1 = [(cooling_time+dwell_time,0),(dwell_time,1),]

                    patt2 = [(clk_width,1),(cooling_time-clk_width+dwell_time+dwell_time,0)]

                    patt3 = [(clk_width,1),(cooling_time-clk_width,0),(clk_width,1),(dwell_time-clk_width,0),(clk_width,1),(dwell_time-clk_width,0)]

                    patt4 = [(cooling_time,1),(dwell_time,1),(dwell_time,1)]

                    patt5 = [(cooling_time+dwell_time+dwell_time,0)]
                    
                    pattA1= [(dwell_time,laser_power),(cooling_time,laser_power),(dwell_time,laser_power)]

                else:
                    patt0 = [(dwell_time+dwell_time,0)]

                    patt1 = [(dwell_time,1),(dwell_time,0)]

                    patt2 = [(clk_width,1),(dwell_time-clk_width+dwell_time,0)]

                    patt3 = [(10,0),(clk_width,1),(dwell_time-clk_width-10,0),(10,0),(clk_width,1),(dwell_time-clk_width-10,0)]

                    patt4 = [(dwell_time,1),(dwell_time,1)]

                    patt5 = [(dwell_time+dwell_time,0)]
                    
                    pattA1= [(dwell_time,laser_power),(dwell_time,laser_power)]


                cwODMRSeq.setDigital(ps_EN_channel, patt0)
                cwODMRSeq.setDigital(ps_CTRL_channel, patt1)
                cwODMRSeq.setDigital(ps_trig_channel, patt2)
                cwODMRSeq.setDigital(ps_clk_channel, patt3)
                cwODMRSeq.setDigital(ps_aom_channel, patt4)
                cwODMRSeq.setDigital(5, patt5)
                cwODMRSeq.setAnalog(ps_aomAnalog_channel, pattA1)


                pulsestreamer.runSequenceInfinitely(cwODMRSeq)

                # Set starting point of Agilent E8257D #2 (MW cycling one)
                agilent2.set_rf_freq(start_freq)
                print('Set E8257D #2 frequency to {freq:.6f} MHz.'.format(freq = start_freq/1e6))
                agilent2.set_rf_amp(mw_power)
                print('Set E8257D #2 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
                agilent2.set_rf_toggle(1)
                print('Turn on RF output of E8257D.')

                for i in range(iterations):
                    signal_null = np.empty(num_points)
                    signal_null[:] = np.nan
                    signal_data.append(np.stack([frequencies/1e6, signal_null]))
                    background_null = np.empty(num_points)
                    background_null[:] = np.nan
                    background_data.append(np.stack([frequencies/1e6, background_null]))
                    power_empty = np.empty(num_points)
                    power_empty[:] = np.nan
                    power_data.append(np.stack([frequencies/1e6, power_empty]))

                    print("Iteration: {iteration}".format(iteration = i+1))

                    for f, freq in enumerate(frequencies):
                        print('Frequency: {frequency:.6f} MHz. Iteration: {iteration}.'.format(frequency = freq/1e6, iteration = i+1))
                        freq = freq.item() # convert numpy.float64() to Python float object
                        agilent2.set_rf_freq(freq) 
                        time.sleep(readout_delay)
                        
                        if cooling_delay:
                            data = daq.readCtrs_singleChannel_externalTrig_externalClk((num_samples)*3, daq_cts_channel,
                                                                                                    daq_trig_channel,
                                                                                                    daq_clk_channel)
                            
                            signal = data[0][1::3]
                            background = data[0][0::3]
                            #print(data)
                            #print(signal)
                            #print(background)
                        else:
                            data = daq.readCtrs_singleChannel_externalTrig_externalClk((num_samples+1)*2, daq_cts_channel,
                                                                                                    daq_trig_channel,
                                                                                                    daq_clk_channel)
                            
                            signal = data[0][1::2]
                            background = data[0][2::2]

                        signal_data[-1][1][f] = np.sum(signal)
                        background_data[-1][1][f] = np.sum(background)


                        signal_data.updated_item(-1)
                        background_data.updated_item(-1)

                        if record_power==True:
                            current_optical_power = pm.get_power() * 1e3 #mW
                        else:
                            current_optical_power = 1.0

                        power_data[-1][1][f] = current_optical_power #mW
                        power_data.updated_item(-1)

                        cwODMRsnspdE8257Dfastswitching_data.push({'params':{'laser_power_V' : laser_power,
                                                    'mw_power_dBm'   : mw_power,
                                                    'mw_start_frequency_MHz': start_freq/1e6,
                                                    'mw_stop_frequency_MHz': stop_freq/1e6,
                                                    'num_points'     : num_points,
                                                    'iterations'     : iterations,
                                                    'readout_delay_ms': readout_delay*1e3,
                                                    'cooling_delay': cooling_delay,
                                                    'duty_cycle_%'     : duty_cycle,
                                                    'cooling_time_ms': cooling_time/1e6,
                                                    'num_samples'    : num_samples,
                                                    'dwell_rate_Hz'  : dwell_rate,
                                                    'dwell_time_us'  : dwell_time/1e3,
                                                    'clk_width_us'   : clk_width/1e3,
                                                    'clk_buffer_us'  : 10,
                                                    'daq_cts_ch'     : daq_cts_channel,
                                                    'daq_trig_ch'    : daq_trig_channel,
                                                    'daq_clk_ch'     : daq_clk_channel,
                                                    'ps_EN_ch'       : ps_EN_channel,
                                                    'ps_CTRL_ch'     : ps_CTRL_channel,
                                                    'ps_trig_ch'     : ps_trig_channel,
                                                    'ps_clk_ch'      : ps_clk_channel,
                                                    'ps_aom_ch'      : ps_aom_channel,
                                                    'ps_aomAnalog_ch': ps_aomAnalog_channel,
                                                    'comments'       : comments,},
                                                'title': 'cwODMR E8257D Fast Switching',
                                                'xlabel': 'Frequency (MHz)',
                                                'ylabel': 'Counts per {t:.3}us'.format(t=dwell_time/1e3),
                                                'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                                'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                                'datasets': {
                                                        'signal' : signal_data,
                                                        'background' : background_data,
                                                        'power' : power_data
                                                }})
                        

                        if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                            # the GUI has asked us nicely to exit
                            return

                # Shutdown
                mwOFF = pulsestreamer.cwODMRmwOFF(1e9)
                pulsestreamer.runSequenceInfinitely(mwOFF)
                #srs.setRfToggle(0)
                agilent2.set_rf_toggle(0)
                print('Done with cwODMRExperiment.')


if __name__ == '__main__':
    exp = cwODMRExperiment()
    exp.cwODMRsnspdExperiment('cwODMRsnspd',1000,2000,5,0.5,2,-21,1,100,50,"/Dev1/PFI1","/Dev1/PFI2","/Dev1/AI0",0,1,2,4)
    #exp.mwPowerTrace(1,-1,'AI0','mwPowerTrace')

