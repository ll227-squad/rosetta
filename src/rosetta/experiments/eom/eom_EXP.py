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

class eomExperiment:
    " "
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
        _logger.info('Created eomExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed eomExperiment instance.')

    def eomSRSScan(self, dataset,
                      laser_power,
                      laser_frequency,
                      mw_power,
                      mw_start_frequency,
                      mw_stop_frequency,
                      log,
                      num_points,
                      iterations,
                      readout_delay,
                      acq_rate,
                      num_samples,
                      SNSPD_channel,
                      comments
                      ):
        with MyInstrumentManager() as mgr, DataSource(dataset) as eomSRSScan_data:
            # Take care of units
            mw_start_frequency = mw_start_frequency*1e6 #Hz
            mw_stop_frequency  = mw_stop_frequency*1e6 #Hz
            readout_delay = readout_delay*1e-3 #s

            #process inputs
            snspd_ch = [int(SNSPD_channel[-1])]

            srs            = mgr.srs_driver
            snspd          = mgr.ni_photonCounting

            times = StreamingList()
            signal_data = StreamingList()

            if log == False:
                frequencies = np.linspace(mw_start_frequency, mw_stop_frequency, num_points)
            else:
                frequencies = np.logspace(np.log10(mw_start_frequency), np.log10(mw_stop_frequency), num_points)

            mw_start_frequency = frequencies[0]
            integrated_counts = 0

            # Set starting point of SRS396
            srs.setFreq(mw_start_frequency)
            print('Set SRS396 frequency to {freq:.6f} MHz.'.format(freq = mw_start_frequency/1e6))
            srs.setRfAmp(mw_power)
            print('Set SRS396 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
            srs.setRfToggle(1)
            srs.setLfToggle(0)
            print('Turn on RF output of SRS396.')

            for i in range(iterations):
                signal_voltages = np.empty(num_points)
                signal_voltages[:] = np.nan
                signal_data.append(np.stack([frequencies/1e6, signal_voltages]))
                for f, freq in enumerate(frequencies):
                    print('Frequency: {frequency:.6f} MHz. Iteration: {iteration}.'.format(frequency = freq/1e6, iteration = i+1))
                    srs.setFreq(freq)
                    srs.setLfToggle(0)
                    time.sleep(readout_delay)
                    # read the number of photon counts received by the photon counter.
                    start_time = time.time()

                    signal_counts = snspd.readCtrs_multi_internalClk(acq_rate, num_samples,snspd_ch)
                    signal_average = np.average(signal_counts)
                    signal_data[-1][1][f] = signal_average
                    end_time = time.time()-start_time
                    # notify the streaminglist that this entry has updated so it will be pushed to the data server
                    signal_data.updated_item(-1)
                    integrated_counts += np.sum(signal_counts)

                    # save the current data to the data server.
                    eomSRSScan_data.push({'params': {'start_freq_MHz': mw_start_frequency/1e6,
                                                 'stop_freq_MHz': mw_stop_frequency/1e6, 
                                                 'log_scale': log,
                                                 'num_points': num_points,
                                                 'iterations': iterations,
                                                 'laser_power_mW':laser_power,
                                                 'laser_frequency_nm': laser_frequency,
                                                 'mw_power_dBm':mw_power,
                                                 'acq_rate' : acq_rate,
                                                 'num_samples' :num_samples,
                                                 'SNSPD_channel': SNSPD_channel,
                                                 'integrated_counts': int(integrated_counts),
                                                 'comments': comments},
                                    'title': 'EOM Scan (Two-Color Experiment)',
                                    'xlabel': 'Frequency (MHz)',
                                    'ylabel': 'Counts per {t:.3}s'.format(t=1/acq_rate),
                                    'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                    'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                    'datasets': {'signal' : signal_data,}
                    })
                    if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                        # the GUI has asked us nicely to exit
                        return

            srs.setRfToggle(0)
            srs.setLfToggle(0)
            srs.setFreq(mw_start_frequency)
            print('Done with eomSRSScanExperiment.')

    def eomSRStransientScan(self, dataset,
                      laser_power,
                      laser_frequency,
                      t_laser_on,
                      t_laser_off,
                      t_aom_delay,
                      mw_power,
                      mw_start_frequency,
                      mw_stop_frequency,
                      num_points,
                      iterations,
                      num_samples,
                      daq_cts_channel,
                      daq_trig_channel,
                      daq_clk_channel,
                      ps_EN_channel,
                      ps_CTRL_channel,
                      ps_trig_channel,
                      ps_clk_channel,
                      ps_aom_channel,
                      ps_aomAnalog_channel,
                      comments
                      ):
        with MyInstrumentManager() as mgr, DataSource(dataset) as eomSRStransientScan_data:
            # Take care of units
            mw_start_frequency = mw_start_frequency*1e6 #Hz
            mw_stop_frequency  = mw_stop_frequency*1e6 #Hz
            t_aom_delay = t_aom_delay*1e3 #ns
            t_laser_on = t_laser_on*1e3 #ns
            t_laser_off = t_laser_off*1e3 #ns
            clk_width = (t_laser_on+t_laser_off)/20 #ns

            #process inputs
            snspd_ch = [int(daq_cts_channel[-1])]

            srs            = mgr.srs_driver
            pulsestreamer  = mgr.pulseStreamer_driver
            daq            = mgr.ni_photonCounting


            times = StreamingList()
            signal_data = StreamingList()

            frequencies = np.linspace(mw_start_frequency, mw_stop_frequency, num_points)

            # Set starting point of SRS396
            srs.setFreq(mw_start_frequency)
            print('Set SRS396 frequency to {freq:.6f} MHz.'.format(freq = mw_start_frequency/1e6))
            srs.setRfAmp(mw_power)
            print('Set SRS396 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
            srs.setRfToggle(1)
            srs.setLfToggle(0)
            print('Turn on RF output of SRS396.')

            # Set PulseStreamer patterns
            seq = pulsestreamer.ps.createSequence()

            patt0 = [(t_aom_delay+t_laser_on+t_laser_off,0)] # rf switch EN

            patt1 = [(t_aom_delay+t_laser_on+t_laser_off,0)] # rf switch CTRL

            patt2 = [(t_aom_delay,0),(clk_width,1),(t_laser_on-clk_width,0),(t_laser_off,0)] # DAQ trigger

            patt3 = [(t_aom_delay,0),(clk_width+10,1),(t_laser_on-clk_width-10,0),(clk_width,1),(t_laser_off-clk_width,0)] # DAQ binning division

            patt4 = [(t_laser_on,1),(t_laser_off+t_aom_delay,0)] # aom digital in

            pattA0 = [(t_laser_on,1.0),(t_laser_off+t_aom_delay,0.0)] # aom analog in, V

            seq.setDigital(ps_EN_channel, patt0)
            seq.setDigital(ps_CTRL_channel, patt1)
            seq.setDigital(ps_trig_channel, patt2)
            seq.setDigital(ps_clk_channel, patt3)
            seq.setDigital(ps_aom_channel, patt4)
            seq.setAnalog(ps_aomAnalog_channel, pattA0)


            pulsestreamer.runSequenceInfinitely(seq)

            for i in range(iterations):
                signal_voltages = np.empty(num_points)
                signal_voltages[:] = np.nan
                signal_data.append(np.stack([frequencies/1e6, signal_voltages]))
                for f, freq in enumerate(frequencies):
                    print('Frequency: {frequency:.6f} MHz. Iteration: {iteration}.'.format(frequency = freq/1e6, iteration = i+1))
                    srs.setFreq(freq)
                    srs.setLfToggle(0)
                    # read the number of photon counts received by the photon counter.
                    start_time = time.time()

                    data = daq.readCtrs_singleChannel_externalTrig_externalClk(num_samples*2, daq_cts_channel,
                                                                                                daq_trig_channel,
                                                                                                daq_clk_channel)
                    end_time = time.time()-start_time
                    signal = data[0][0::2]
                    print(end_time)

                    signal_data[-1][1][f] = np.sum(signal)

                    
                    # notify the streaminglist that this entry has updated so it will be pushed to the data server
                    signal_data.updated_item(-1)

                    # save the current data to the data server.
                    eomSRStransientScan_data.push({'params': {'start_freq_MHz': mw_start_frequency/1e6,
                                                 'stop_freq_MHz': mw_stop_frequency/1e6, 
                                                 'num_points': num_points,
                                                 'iterations': iterations,
                                                 't_aom_delay_us': t_aom_delay/1e3,
                                                 't_laser_on_us': t_laser_on/1e3,
                                                 't_laser_off_us': t_laser_off/1e3,
                                                 'laser_power_mW':laser_power,
                                                 'laser_frequency_nm': laser_frequency,
                                                 'mw_power_dBm':mw_power,
                                                 'num_samples' :num_samples,
                                                 'SNSPD_channel': daq_cts_channel,
                                                 'DAQ_trig_channel':daq_trig_channel,
                                                 'DAQ_clk_channel':daq_clk_channel,
                                                 'ps_EN_channel':ps_EN_channel,
                                                 'ps_CTRL_channel':ps_CTRL_channel,
                                                 'ps_trig_channel':ps_trig_channel,
                                                 'ps_clk_channel':ps_clk_channel,
                                                 'ps_aom_channel':ps_aom_channel,
                                                 'ps_aomAnalog_channel':ps_aomAnalog_channel,
                                                 'comments': comments},
                                    'title': 'EOM Scan (Two-Color Experiment)',
                                    'xlabel': 'Frequency (MHz)',
                                    'ylabel': 'Counts per {t:.3}s'.format(t=t_laser_on/1e9),
                                    'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                    'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                    'datasets': {'signal' : signal_data,}
                    })
                    if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                        # the GUI has asked us nicely to exit
                        return

            srs.setRfToggle(0)
            srs.setLfToggle(0)
            srs.setFreq(mw_start_frequency)
            print('Done with eomSRStransientScanExperiment.')

    def eomE8257DScan(self, dataset,
                      laser_power,
                      laser_frequency,
                      mw_power,
                      mw_start_frequency,
                      mw_stop_frequency,
                      log,
                      num_points,
                      iterations,
                      readout_delay,
                      acq_rate,
                      num_samples,
                      SNSPD_channel,
                      comments
                      ):
        with MyInstrumentManager() as mgr, DataSource(dataset) as eomSRSScan_data:
            # Take care of units
            mw_start_frequency = mw_start_frequency*1e6 #Hz
            mw_stop_frequency  = mw_stop_frequency*1e6 #Hz
            readout_delay = readout_delay*1e-3 #s

            #process inputs
            snspd_ch = [int(SNSPD_channel[-1])] 

            agilent        = mgr.e8257d_driver
            snspd          = mgr.ni_photonCounting

            times = StreamingList()
            signal_data = StreamingList()

            if log == False:
                frequencies = np.linspace(mw_start_frequency, mw_stop_frequency, num_points)
            else:
                frequencies = np.logspace(np.log10(mw_start_frequency), np.log10(mw_stop_frequency), num_points)

            # Set starting point of E8257D
            agilent.set_rf_freq(mw_start_frequency)
            print('Set E8257D frequency to {freq:.6f} MHz.'.format(freq = mw_start_frequency/1e6))
            agilent.set_rf_amp(mw_power)
            print('Set E8257D output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
            agilent.set_rf_toggle(1)
            print('Turn on RF output of SRS396.')

            for i in range(iterations):
                signal_voltages = np.empty(num_points)
                signal_voltages[:] = np.nan
                signal_data.append(np.stack([frequencies/1e6, signal_voltages]))
                for f, freq in enumerate(frequencies):
                    print('Frequency: {frequency:.6f} MHz. Iteration: {iteration}.'.format(frequency = freq/1e6, iteration = i+1))
                    agilent.set_rf_freq(freq)
                    time.sleep(readout_delay)
                    # read the number of photon counts received by the photon counter.
                    start_time = time.time()

                    signal = np.average(snspd.readCtrs_multi_internalClk(acq_rate, num_samples,snspd_ch))
                    signal_data[-1][1][f] = signal
                    end_time = time.time()-start_time
                    # notify the streaminglist that this entry has updated so it will be pushed to the data server
                    signal_data.updated_item(-1)

                    # save the current data to the data server.
                    eomSRSScan_data.push({'params': {'start_freq_MHz': mw_start_frequency/1e6,
                                                 'stop_freq_MHz': mw_stop_frequency/1e6, 
                                                 'log_scale' : log,
                                                 'num_points': num_points,
                                                 'iterations': iterations,
                                                 'laser_power_mW':laser_power,
                                                 'laser_frequency_nm': laser_frequency,
                                                 'mw_power_dBm':mw_power,
                                                 'acq_rate' : acq_rate,
                                                 'num_samples' :num_samples,
                                                 'SNSPD_channel': SNSPD_channel,
                                                 'comments': comments},
                                    'title': 'EOM Scan (Two-Color Experiment) with E8257D',
                                    'xlabel': 'Frequency (MHz)',
                                    'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                    'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                    'ylabel': 'Counts per {t:.3}s'.format(t=1/acq_rate),
                                    'datasets': {'signal' : signal_data,}
                    })
                    if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                        # the GUI has asked us nicely to exit
                        return

            agilent.set_rf_toggle(0)
            agilent.set_rf_freq(mw_start_frequency)
            print('Done with eomE8257DScanExperiment.')

    def eomE8257DwithMWcyclingScan(self, dataset,
                      laser_power,
                      laser_frequency,
                      cycle_mw_power,
                      cycle_mw_frequency,
                      cycle_mw_off_on,
                      mw_power,
                      mw_start_frequency,
                      mw_stop_frequency,
                      num_points,
                      iterations,
                      readout_delay,
                      acq_rate,
                      num_samples,
                      SNSPD_channel,
                      ps_channel_EN,
                      ps_channel_CTRL,
                      ps_channel_DAQ,
                      ps_channel_AOM,
                      comments
                      ):
        with MyInstrumentManager() as mgr, DataSource(dataset) as eomSRSScan_data:
            # Take care of units
            cycle_mw_frequency = cycle_mw_frequency*1e6 #Hz
            mw_start_frequency = mw_start_frequency*1e6 #Hz
            mw_stop_frequency  = mw_stop_frequency*1e6 #Hz
            readout_delay = readout_delay*1e-3 #s

            #process inputs
            snspd_ch = [int(SNSPD_channel[-1])]

            agilent        = mgr.e8257d_driver # EOM
            agilent2       = mgr.e8257d_driver2 # cycling MWs
            snspd          = mgr.ni_photonCounting
            pulsestreamer  = mgr.pulseStreamer_driver

            times = StreamingList()
            signal_mw_on_data = StreamingList()
            signal_mw_off_data = StreamingList()

            frequencies = np.linspace(mw_start_frequency, mw_stop_frequency, num_points)

            # Set starting point of E8257D for EOM
            agilent.set_rf_freq(mw_start_frequency)
            print('Set E8257D (EOM) frequency to {freq:.6f} MHz.'.format(freq = mw_start_frequency/1e6))
            agilent.set_rf_amp(mw_power)
            print('Set E8257D (EOM) output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
            agilent.set_rf_toggle(1)
            print('Turn on RF output of E8257D (EOM).')

            # Set starting point of E8257D for MW cycling
            agilent2.set_rf_freq(cycle_mw_frequency)
            print('Set E8257D (cycling MWs) frequency to {freq:.6f} MHz.'.format(freq = cycle_mw_frequency/1e6))
            agilent2.set_rf_amp(cycle_mw_power)
            print('Set E8257D (cycling MWs) output amplitude to {amp:.2f} dBm.'.format(amp= cycle_mw_power))
            agilent2.set_rf_toggle(cycle_mw_off_on)
            print('Turn {onoff} RF output of E8257D (cycling MWs).'.format(onoff = cycle_mw_off_on))

            mwON = pulsestreamer.ps.createSequence()
            mwON.setDigital(ps_channel_EN, [(num_samples/acq_rate*1e9,0)])
            mwON.setDigital(ps_channel_CTRL, [(num_samples/acq_rate*1e9,1)])
            mwON.setDigital(ps_channel_DAQ, [(num_samples/acq_rate*1e9,1)])
            mwON.setDigital(ps_channel_AOM, [(num_samples/acq_rate*1e9,1)])

            mwOFF = pulsestreamer.ps.createSequence()
            mwOFF.setDigital(ps_channel_EN, [(num_samples/acq_rate*1e9,0)])
            mwOFF.setDigital(ps_channel_CTRL, [(num_samples/acq_rate*1e9,0)])
            mwOFF.setDigital(ps_channel_DAQ, [(num_samples/acq_rate*1e9,1)])
            mwOFF.setDigital(ps_channel_AOM, [(num_samples/acq_rate*1e9,1)])

            for i in range(iterations):
                signal_voltages = np.empty(num_points)
                signal_voltages[:] = np.nan
                signal_mw_off_data.append(np.stack([frequencies/1e6, signal_voltages]))
                signal_mw_on_data.append(np.stack([frequencies/1e6, signal_voltages]))
                for f, freq in enumerate(frequencies):
                    print('Frequency: {frequency:.6f} MHz. Iteration: {iteration}.'.format(frequency = freq/1e6, iteration = i+1))
                    
                    pulsestreamer.runSequenceInfinitely(mwON)
                    agilent.set_rf_freq(freq)
                    time.sleep(readout_delay)
                    # read the number of photon counts received by the photon counter.
                    start_time = time.time()

                    signal = np.average(snspd.readCtrs_multi_internalClk(acq_rate, num_samples,snspd_ch))
                    signal_data[-1][1][f] = signal
                    end_time = time.time()-start_time
                    # notify the streaminglist that this entry has updated so it will be pushed to the data server
                    signal_data.updated_item(-1)

                    # save the current data to the data server.
                    eomSRSScan_data.push({'params': {
                                                 'cycling_MWs_freq_MHz': cycle_mw_frequency/1e6,
                                                 'cycling_MWs_power_dBm' : cycle_mw_power,
                                                 'cycling_MWs_on_or_off' : cycle_mw_off_on,
                                                 'start_freq_MHz': mw_start_frequency/1e6,
                                                 'stop_freq_MHz': mw_stop_frequency/1e6, 
                                                 'num_points': num_points,
                                                 'iterations': iterations,
                                                 'laser_power_mW':laser_power,
                                                 'laser_frequency_nm': laser_frequency,
                                                 'mw_power_dBm':mw_power,
                                                 'acq_rate' : acq_rate,
                                                 'num_samples' :num_samples,
                                                 'SNSPD_channel': SNSPD_channel,
                                                 'comments': comments},
                                    'title': 'EOM Scan (Two-Color Experiment) with E8257D',
                                    'xlabel': 'Frequency (MHz)',
                                    'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                    'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                    'ylabel': 'Counts per {t:.3}s'.format(t=1/acq_rate),
                                    'datasets': {'signal' : signal_data,}
                    })
                    if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                        # the GUI has asked us nicely to exit
                        return

            agilent.set_rf_toggle(0)
            agilent.set_rf_freq(mw_start_frequency)
            print('Done with eomE8257DwithMWcyclingScanExperiment.')