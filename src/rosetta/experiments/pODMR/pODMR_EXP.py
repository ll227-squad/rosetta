import time
import logging
from pathlib import Path
from itertools import count
import numpy as np
from nspyre import nspyre_init_logger
from nspyre import StreamingList, DataSource, experiment_widget_process_queue

from rosetta.insmgr import MyInstrumentManager
from rpyc.utils.classic import obtain

_HERE = Path(__file__).parent
_logger = logging.getLogger(__name__)

class pODMRExperiment:
    " Different flavors of pODMR"
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
        _logger.info('Created pODMRExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed pODMRExperiment instance.')

    def pODMRExperiment(self,
                           dataset:str,
                           laser_power,
                           mw_power,
                           mw_frequency_min,
                           mw_frequency_max,
                           t_aom_delay,
                           t_init,
                           t_mw_delay,
                           t_rabi,
                           num_points,
                           iterations,
                           t_readout_delay,
                           t_readout,
                           num_samples,
                           cooling_delay,
                           cooling_wait,
                           daq_cts_channel,
                           daq_trig_channel,
                           daq_clk_channel,
                           ps_EN_channel,
                           ps_CTRL_channel,
                           ps_trig_channel,
                           ps_clk_channel,
                           ps_aom_channel,
                           ps_aomAnalog_channel,
                           comments,):
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as pODMR_data:
                # Take care of units
                mw_frequency_min = mw_frequency_min*1e6 #Hz
                mw_frequency_max = mw_frequency_max*1e6 #Hz
                t_aom_delay = t_aom_delay*1e3 #ns
                t_init = t_init*1e3 # ns
                t_mw_delay = t_mw_delay*1e3 #ns
                t_rabi = t_rabi*1e3 #ns
                t_readout_delay = t_readout_delay*1e3 #ns
                t_readout = t_readout*1e3 #ns
                clk_width = t_readout/2
                cooling_wait = cooling_wait*1e3 #ns

                srs = mgr.srs_driver
                agilent2 = mgr.e8257d_driver2
                daq = mgr.ni_photonCounting
                pulsestreamer = mgr.pulseStreamer_driver

                times = StreamingList()
                signal_data = StreamingList()
                background_data = StreamingList()

                freqs = np.linspace(mw_frequency_min,mw_frequency_max, num_points)

                # Set starting point of SRS396
                #srs.setFreq(mw_frequency_min)
                #srs.setRfAmp(mw_power)
                #srs.setRfToggle(1)

                # Set starting point of Agilent E8257D #2 (MW cycling one)
                agilent2.set_rf_freq(mw_frequency_min)
                print('Set E8257D #2 frequency to {freq:.6f} MHz.'.format(freq = mw_frequency_min/1e6))
                agilent2.set_rf_amp(mw_power)
                print('Set E8257D #2 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
                agilent2.set_rf_toggle(1)
                print('Turn on RF output of E8257D #2.')

                for i in range(iterations):
                    signal_null = np.empty(num_points)
                    signal_null[:] = np.nan
                    signal_data.append(np.stack([freqs/1e6, signal_null]))
                    background_null = np.empty(num_points)
                    background_null[:] = np.nan
                    background_data.append(np.stack([freqs/1e6, background_null]))

                    # set pulse streamer pattern
                    seq = pulsestreamer.ps.createSequence()
                    
                    if cooling_delay:

                        patt0 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout+clk_width+cooling_wait,0),
                                            (t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout+clk_width+cooling_wait,0)]

                        patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(t_rabi,1),(t_readout_delay+t_readout+clk_width+cooling_wait,0),
                                            (t_init+t_mw_delay,0),(t_rabi,0),(t_readout_delay+t_readout+clk_width+cooling_wait,0)]

                        patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout-clk_width+clk_width+cooling_wait,0),
                                                (clk_width,0),(t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout-clk_width+clk_width+cooling_wait,0)]

                        patt3 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(cooling_wait,0),
                                            (t_init+t_mw_delay+t_rabi+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(cooling_wait,0)]

                        patt4 = [(t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,1),(clk_width+cooling_wait,0),
                                (t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,1),(clk_width+cooling_wait+t_aom_delay,0)]
                        
                        patt5 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout+clk_width+cooling_wait,0),
                                            (t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout+clk_width+cooling_wait,0)]
                        
                        pattA1 = [(t_init,laser_power),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,laser_power),(clk_width+cooling_wait,0),
                                (t_init,laser_power),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,laser_power),(clk_width+cooling_wait+t_aom_delay,0)]
                        
                    else:
                        patt0 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout+clk_width,0),
                                            (t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout+clk_width,0)]

                        patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(t_rabi,1),(t_readout_delay+t_readout+clk_width,0),
                                            (t_init+t_mw_delay,0),(t_rabi,0),(t_readout_delay+t_readout+clk_width,0)]

                        patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout-clk_width+clk_width,0),
                                                (clk_width,0),(t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout-clk_width+clk_width,0)]

                        patt3 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),
                                            (t_init+t_mw_delay+t_rabi+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1)]

                        patt4 = [(t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,1),(clk_width,0),
                                (t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,1),(clk_width+t_aom_delay,0)]
                        
                        patt5 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout+clk_width,0),
                                            (t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout+clk_width,0)]
                        
                        pattA1 = [(t_init,laser_power),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,laser_power),(clk_width,0),
                                (t_init,laser_power),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,laser_power),(clk_width+t_aom_delay,0)]
                    
                    seq.setDigital(ps_EN_channel, patt0)
                    seq.setDigital(ps_CTRL_channel, patt1)
                    seq.setDigital(ps_trig_channel, patt2)
                    seq.setDigital(ps_clk_channel, patt3)
                    seq.setDigital(ps_aom_channel, patt4)
                    seq.setDigital(5, patt5)
                    seq.setAnalog(ps_aomAnalog_channel, pattA1)

                    pulsestreamer.runSequenceInfinitely(seq)

                    print("Iteration: {iteration}".format(iteration = i+1))
                    for f, freq in enumerate(freqs):
                        freq = freq.item()
                        #srs.setFreq(freq)
                        agilent2.set_rf_freq(freq)
                        
                        data = daq.readCtrs_singleChannel_externalTrig_externalClk(num_samples*4, daq_cts_channel,
                                                                                                  daq_trig_channel,
                                                                                                  daq_clk_channel)
                        
                        signal = data[0][0::4]
                        background = data[0][2::4]
                        #print(data)
                        #print(signal)
                        #print(background)

                        signal_data[-1][1][f] = np.sum(signal)
                        background_data[-1][1][f] = np.sum(background)

                        signal_data.updated_item(-1)
                        background_data.updated_item(-1)

                        pODMR_data.push({'params':{'laser_power_V' : laser_power,
                                                    'mw_power_dBm'   : mw_power,
                                                    'mw_frequency_min_MHz': mw_frequency_min/1e6,
                                                    'mw_frequency_max_MHz': mw_frequency_max/1e6,
                                                    'num_points'     : num_points,
                                                    'iterations'     : iterations,
                                                    'num_samples'    : num_samples,
                                                    't_aom_delay_us' : t_aom_delay/1e3,
                                                    't_init_us'      : t_init/1e3,
                                                    't_mw_delay_us'  : t_mw_delay/1e3,
                                                    't_rabi_us'      : t_rabi/1e3,
                                                    't_readout_delay_us' : t_readout_delay/1e3,
                                                    't_readout_us'   : t_readout/1e3,
                                                    'clk_width_us'   : clk_width/1e3,
                                                    'cooling_delay'  : cooling_delay,
                                                    'cooling_wait_us': cooling_wait/1e3,
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
                                                'title': 'pulsed ODMR',
                                                'xlabel': 'MW Frequency (MHz)',
                                                'ylabel': 'Counts per {t:.3}s'.format(t=t_readout/1e9),
                                                'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                                'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                                'datasets': {
                                                        'signal' : signal_data,
                                                        'background' : background_data
                                                }})
                        if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                            # the GUI has asked us nicely to exit
                            return

                # Shutdown
                mwOFF = pulsestreamer.cwODMRmwOFF(1e9)
                pulsestreamer.runSequenceInfinitely(mwOFF)
                #srs.setRfToggle(0)
                agilent2.set_rf_toggle(0)
                print('Done with pODMRExperiment.')

    def pODMRabbrExperiment(self,
                           dataset:str,
                           laser_power,
                           mw_power,
                           mw_frequency_min,
                           mw_frequency_max,
                           t_aom_delay,
                           t_init,
                           t_mw_delay,
                           t_rabi,
                           num_points,
                           iterations,
                           t_readout_delay,
                           t_readout,
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
                           comments,):
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as pODMRabbr_data:
                # Take care of units
                mw_frequency_min = mw_frequency_min*1e6 #Hz
                mw_frequency_max = mw_frequency_max*1e6 #Hz
                t_aom_delay = t_aom_delay*1e3 #ns
                t_init = t_init*1e3 # ns
                t_mw_delay = t_mw_delay*1e3 #ns
                t_rabi = t_rabi*1e3 #ns
                t_readout_delay = t_readout_delay*1e3 #ns
                t_readout = t_readout*1e3 #ns
                clk_width = t_readout/2

                srs = mgr.srs_driver
                agilent2 = mgr.e8257d_driver2
                daq = mgr.ni_photonCounting
                pulsestreamer = mgr.pulseStreamer_driver

                times = StreamingList()
                signal_data = StreamingList()
                background_data = StreamingList()

                freqs = np.linspace(mw_frequency_min,mw_frequency_max, num_points)

                # Set starting point of Agilent E8257D #2 (MW cycling one)
                agilent2.set_rf_freq(mw_frequency_min)
                print('Set E8257D #2 frequency to {freq:.6f} MHz.'.format(freq = mw_frequency_min/1e6))
                agilent2.set_rf_amp(mw_power)
                print('Set E8257D #2 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
                agilent2.set_rf_toggle(1)
                print('Turn on RF output of E8257D #2.')

                for i in range(iterations):
                    signal_null = np.empty(num_points)
                    signal_null[:] = np.nan
                    signal_data.append(np.stack([freqs/1e3, signal_null]))
                    background_null = np.empty(num_points)
                    background_null[:] = np.nan
                    background_data.append(np.stack([freqs/1e3, background_null]))

                    # set pulse streamer pattern
                    seq = pulsestreamer.ps.createSequence()
                    
                    patt0 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay+t_init,0)]

                    patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(t_rabi,1),(t_readout_delay+t_init,0)]

                    patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+t_mw_delay+t_rabi+t_readout_delay+t_init-clk_width,0)]

                    patt3 = [(t_aom_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-t_readout-clk_width+t_mw_delay+t_rabi+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-t_readout-clk_width,0)]

                    #patt4 = [(t_aom_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,0),(t_init-t_readout-clk_width+t_mw_delay+t_rabi+t_readout_delay,0),(clk_width,0),(t_readout-clk_width,0),(clk_width,0),(t_init-t_readout-clk_width,0)]
                    #pattA1 =[(t_aom_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,0),(t_init-t_readout-clk_width+t_mw_delay+t_rabi+t_readout_delay,0),(clk_width,0),(t_readout-clk_width,0),(clk_width,0),(t_init-t_readout-clk_width,0)]
                    patt4 = [(t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_init+t_aom_delay,1)]
                    pattA1 = [(t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_init+t_aom_delay,1)]
                    
                    seq.setDigital(ps_EN_channel, patt0)
                    seq.setDigital(ps_CTRL_channel, patt1)
                    seq.setDigital(ps_trig_channel, patt2)
                    seq.setDigital(ps_clk_channel, patt3)
                    seq.setDigital(ps_aom_channel, patt4)
                    seq.setAnalog(ps_aomAnalog_channel, pattA1)

                    pulsestreamer.runSequenceInfinitely(seq)

                    print("Iteration: {iteration}".format(iteration = i+1))
                    for f, freq in enumerate(freqs):
                        freq = freq.item()
                        agilent2.set_rf_freq(freq)
                        time.sleep(0.1)
                        
                        data = daq.readCtrs_singleChannel_externalTrig_externalClk(num_samples*4, daq_cts_channel,
                                                                                                  daq_trig_channel,
                                                                                                  daq_clk_channel)
                        
                        background = data[0][3:][0::4]
                        signal = data[0][3:][2::4]
                        #print(data)
                        #print(signal)
                        #print(background)

                        signal_data[-1][1][f] = np.sum(signal)
                        background_data[-1][1][f] = np.sum(background)

                        signal_data.updated_item(-1)
                        background_data.updated_item(-1)

                        pODMRabbr_data.push({'params':{'laser_power_mW' : laser_power,
                                                    'mw_power_dBm'   : mw_power,
                                                    'mw_frequency_min_MHz': mw_frequency_min/1e6,
                                                    'mw_frequency_max_MHz': mw_frequency_max/1e6,
                                                    'num_points'     : num_points,
                                                    'iterations'     : iterations,
                                                    'num_samples'    : num_samples,
                                                    't_aom_delay_us' : t_aom_delay/1e3,
                                                    't_init_us'      : t_init/1e3,
                                                    't_mw_delay_us'  : t_mw_delay/1e3,
                                                    't_rabi_us'      : t_rabi/1e3,
                                                    't_readout_delay_us' : t_readout_delay/1e3,
                                                    't_readout_us'   : t_readout/1e3,
                                                    'clk_width_us'   : clk_width/1e3,
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
                                                'title': 'pulsed ODMR',
                                                'xlabel': 'MW Frequency (MHz)',
                                                'ylabel': 'Counts per {t:.3}s'.format(t=t_readout/1e9),
                                                'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                                'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                                'datasets': {
                                                        'signal' : signal_data,
                                                        'background' : background_data
                                                }})
                        if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                            # the GUI has asked us nicely to exit
                            return

                # Shutdown
                mwOFF = pulsestreamer.cwODMRmwOFF(1e9)
                pulsestreamer.runSequenceInfinitely(mwOFF)
                srs.setRfToggle(0)
                print('Done with pODMRExperiment.')

    def pODMRabsoluteExperiment(self,
                           dataset:str,
                           laser_power,
                           mw_power,
                           mw_frequency_min,
                           mw_frequency_max,
                           t_aom_delay,
                           t_init,
                           t_mw_delay,
                           t_mw,
                           t_readout_delay,
                           t_readout,
                           t_wait,
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
                           comments,):
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as pODMRabsolute_data:
                # Take care of units
                mw_frequency_min = mw_frequency_min*1e6 #Hz
                mw_frequency_max = mw_frequency_max*1e6 #Hz
                t_aom_delay = t_aom_delay*1e3 #ns
                t_init = t_init*1e3 # ns
                t_mw_delay = t_mw_delay*1e3 #ns
                t_mw = t_mw*1e3 #ns
                t_readout_delay = t_readout_delay*1e3 #ns
                t_readout = t_readout*1e3 #ns
                t_wait = t_wait*1e3 #ns
                clk_width = t_readout/2

                srs = mgr.srs_driver
                agilent2 = mgr.e8257d_driver2
                daq = mgr.ni_photonCounting
                pulsestreamer = mgr.pulseStreamer_driver

                times = StreamingList()
                signal_data = StreamingList()
                background_data = StreamingList()

                freqs = np.linspace(mw_frequency_min,mw_frequency_max, num_points)

                # Set starting point of SRS396
                #srs.setFreq(mw_frequency_min)
                #srs.setRfAmp(mw_power)
                #srs.setRfToggle(1)

                # Set starting point of Agilent E8257D #2 (MW cycling one)
                agilent2.set_rf_freq(mw_frequency_min)
                print('Set E8257D #2 frequency to {freq:.6f} MHz.'.format(freq = mw_frequency_min/1e6))
                agilent2.set_rf_amp(mw_power)
                print('Set E8257D #2 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
                agilent2.set_rf_toggle(1)
                print('Turn on RF output of E8257D #2.')

                for i in range(iterations):
                    signal_null = np.empty(num_points)
                    signal_null[:] = np.nan
                    signal_data.append(np.stack([freqs/1e3, signal_null]))
                    background_null = np.empty(num_points)
                    background_null[:] = np.nan
                    background_data.append(np.stack([freqs/1e3, background_null]))

                    # set pulse streamer pattern
                    seq = pulsestreamer.ps.createSequence()
                    
                    patt0 = [(t_aom_delay+t_init+t_wait+clk_width,0),
                                         (t_init+t_wait+clk_width,0)]

                    patt1 = [(t_aom_delay+t_mw_delay,0),(t_mw,1),(t_init+t_wait-t_mw_delay-t_mw+clk_width,0),
                                         (t_mw_delay,0),(t_mw,0),(t_init+t_wait-t_mw_delay-t_mw+clk_width,0)]

                    patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+t_wait-clk_width+clk_width,0),
                                             (clk_width,0),(t_init+t_wait-clk_width+clk_width,0)]

                    patt3 = [(t_aom_delay+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init+t_wait-t_readout_delay-t_readout,0),
                                         (t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init+t_wait-t_readout_delay-t_readout,0)]

                    patt4 = [(t_init,1),(t_wait+clk_width,0),
                             (t_init,1),(t_wait+clk_width+t_aom_delay,0)]
                    
                    patt4 = [(t_init,1),(t_readout_delay-t_init,1),(t_readout,1),(t_wait-(t_readout_delay-t_init)-t_readout+clk_width,0),
                             (t_init,1),(t_readout_delay-t_init,1),(t_readout,1),(t_wait-(t_readout_delay-t_init)-t_readout+clk_width+t_aom_delay,0)]
                    
                    pattA1 = [(t_init,1),(t_wait+clk_width,0),
                              (t_init,1),(t_wait+clk_width+t_aom_delay,0)]
                    
                    pattA1 = [(t_init,1),(t_readout_delay-t_init,0),(t_readout,1),(t_wait-(t_readout_delay-t_init)-t_readout+clk_width,0),
                              (t_init,1),(t_readout_delay-t_init,0),(t_readout,1),(t_wait-(t_readout_delay-t_init)-t_readout+clk_width+t_aom_delay,0)]
                    
                    seq.setDigital(ps_EN_channel, patt0)
                    seq.setDigital(ps_CTRL_channel, patt1)
                    seq.setDigital(ps_trig_channel, patt2)
                    seq.setDigital(ps_clk_channel, patt3)
                    seq.setDigital(ps_aom_channel, patt4)
                    seq.setAnalog(ps_aomAnalog_channel, pattA1)

                    pulsestreamer.runSequenceInfinitely(seq)

                    print("Iteration: {iteration}".format(iteration = i+1))
                    for f, freq in enumerate(freqs):
                        freq = freq.item()
                        #srs.setFreq(freq)
                        agilent2.set_rf_freq(freq)
                        
                        data = daq.readCtrs_singleChannel_externalTrig_externalClk(num_samples*4, daq_cts_channel,
                                                                                                  daq_trig_channel,
                                                                                                  daq_clk_channel)
                        
                        signal = data[0][0::4]
                        background = data[0][2::4]
                        #print(data)
                        #print(signal)
                        #print(background)

                        signal_data[-1][1][f] = np.sum(signal)
                        background_data[-1][1][f] = np.sum(background)

                        signal_data.updated_item(-1)
                        background_data.updated_item(-1)

                        pODMRabsolute_data.push({'params':{'laser_power_mW' : laser_power,
                                                    'mw_power_dBm'   : mw_power,
                                                    'mw_frequency_min_MHz': mw_frequency_min/1e6,
                                                    'mw_frequency_max_MHz': mw_frequency_max/1e6,
                                                    'num_points'     : num_points,
                                                    'iterations'     : iterations,
                                                    'num_samples'    : num_samples,
                                                    't_aom_delay_us' : t_aom_delay/1e3,
                                                    't_init_us'      : t_init/1e3,
                                                    't_mw_delay_us'  : t_mw_delay/1e3,
                                                    't_mw_us'        : t_mw/1e3,
                                                    't_readout_delay_us' : t_readout_delay/1e3,
                                                    't_readout_us'   : t_readout/1e3,
                                                    't_wait_us'      : t_wait/1e3,
                                                    'clk_width_us'   : clk_width/1e3,
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
                                                'title': 'pODMR, mw and readout delays relative to t=0',
                                                'xlabel': 'MW Frequency (MHz)',
                                                'ylabel': 'Counts per {t:.3}s'.format(t=t_readout/1e9),
                                                'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                                'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                                'datasets': {
                                                        'signal' : signal_data,
                                                        'background' : background_data
                                                }})
                        if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                            # the GUI has asked us nicely to exit
                            return

                # Shutdown
                mwOFF = pulsestreamer.cwODMRmwOFF(1e9)
                pulsestreamer.runSequenceInfinitely(mwOFF)
                #srs.setRfToggle(0)
                agilent2.set_rf_toggle(0)
                print('Done with pODMRabsoluteExperiment.')
                        
if __name__ == '__main__':
    exp = pODMRExperiment()
    exp.pODMRExperiment(dataset='pODMR',
                        laser_power=1,
                        mw_power=-50,
                        mw_frequency_min=1352,
                        mw_frequency_max=1353,
                        t_aom_delay=1.1, #us
                        t_init=1000, #us
                        t_mw_delay=1, #us
                        t_rabi=0.050, #us
                        num_points = 6, # how many taus
                        iterations =2, # how many times to repeat measurement at each tau
                        t_readout_delay = 1, #us
                        t_readout = 50, #us
                        num_samples = 10, # how many averages to perform at each tau in one iteration
                        daq_cts_channel = "/Dev1/PFI1",
                        daq_trig_channel = "/Dev1/PFI2",
                        daq_clk_channel = "/Dev1/PFI3",
                        ps_EN_channel = 0,
                        ps_CTRL_channel = 1,
                        ps_trig_channel = 2,
                        ps_clk_channel = 3,
                        ps_aom_channel = 4,
                        comments = 'none')

