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

class t1Experiment:
    " Different flavors of T1 measurements"
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
        _logger.info('Created t1Experiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed t1Experiment instance.')

    def t1Experiment(self,
                     dataset,
                     laser_wavelength,
                     laser_power,
                     t_aom_delay,
                     t_init,
                     num_points,
                     iterations,
                     t_readout_delay_min,
                     t_readout_delay_max,
                     t_readout,
                     t_wait,
                     num_samples,
                     log,
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
                     comments,):
        with MyInstrumentManager() as mgr, DataSource(dataset) as t1_data:
            t_aom_delay = t_aom_delay*1e3 #ns
            t_init = t_init*1e3 #ns
            t_readout_delay_min = t_readout_delay_min*1e3 #ns
            t_readout_delay_max = t_readout_delay_max*1e3 #ns
            t_readout = t_readout*1e3 #ns
            t_wait = t_wait*1e3 #ns
            clk_width = t_readout/2

            daq = mgr.ni_photonCounting
            pulsestreamer = mgr.pulseStreamer_driver
            if record_power==True:
                pm  = mgr.powerMeter_driver
                pm.set_correction_wavelength(laser_wavelength) # send as nm
                calibration_wavelength = pm.get_correction_wavelength()
            else:
                calibration_wavelength = None

            signal_data = StreamingList()
            init_data = StreamingList()
            power_data = StreamingList()

            if log == False:
                taus = np.linspace(t_readout_delay_min,  t_readout_delay_max, num_points)
            else:
                taus = np.logspace(np.log10(t_readout_delay_min), np.log10(t_readout_delay_max), num_points)

            integrated_counts = 0

            for i in range(iterations):
                signal_null = np.empty(num_points)
                signal_null[:] = np.nan
                signal_data.append(np.stack([taus/1e3, signal_null]))

                init_null = np.empty(num_points)
                init_null[:] = np.nan
                init_data.append(np.stack([taus/1e3, init_null]))

                power_empty = np.empty(num_points)
                power_empty[:] = np.nan
                power_data.append(np.stack([taus, power_empty]))

                print("Iteration: {iteration}".format(iteration = i+1))

                for t, tau in enumerate(taus):
                    # tau = readout delay (variable)
                    seq = pulsestreamer.ps.createSequence()
                    tau = tau.item() # convert numpy.float64() to Python float object

                    patt0 = [(t_aom_delay+t_init+tau+t_readout+t_readout_delay_max-tau+clk_width+t_wait,0)]

                    patt1 = [(t_aom_delay+t_init+tau+t_readout+t_readout_delay_max-tau+clk_width,0),(t_wait,0)]

                    patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+tau+t_readout+t_readout_delay_max-tau-clk_width+clk_width+t_wait,0)]

                    patt3 = [(t_aom_delay+100,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-clk_width-t_readout-100+tau,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_readout_delay_max-tau+t_wait,0)]
                    #patt3 = [(t_aom_delay+t_init+tau,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_readout_delay_max-tau+t_wait,0)]

                    patt4 = [(t_init,1),(tau,0),(t_readout,1),(t_readout_delay_max-tau+clk_width+t_wait+t_aom_delay,0)]

                    pattA1 = [(t_init,laser_power),(tau,0.0),(t_readout,laser_power),(t_readout_delay_max-tau+clk_width+t_wait+t_aom_delay,0.0)]

                    seq.setDigital(ps_EN_channel, patt0)
                    seq.setDigital(ps_CTRL_channel, patt1)
                    seq.setDigital(ps_trig_channel, patt2)
                    seq.setDigital(ps_clk_channel, patt3)
                    seq.setDigital(ps_aom_channel, patt4)
                    seq.setAnalog(ps_aomAnalog_channel, pattA1)


                    pulsestreamer.runSequenceInfinitely(seq)

                    if record_power==True:
                        current_optical_power = pm.get_power() * 1e3 #mW
                    else:
                        current_optical_power = 1.0
                    
                    data = daq.readCtrs_singleChannel_externalTrig_externalClk(num_samples*4, daq_cts_channel,
                                                                                                daq_trig_channel,
                                                                                                daq_clk_channel)
                    
                    #print(data)
                    #signal = data[0][0::4]
                    #print(np.sum(signal))
                    #print(data)

                    init = data[0][0::4]
                    signal = data[0][2::4]

                    #print(signal)
                    #print(init)

                    init_data[-1][1][t] = np.sum(init)
                    signal_data[-1][1][t] = np.sum(signal)
                    power_data[-1][1][t] = current_optical_power #mW
                    integrated_counts += np.sum(signal)
                    

                    init_data.updated_item(-1)
                    signal_data.updated_item(-1)
                    power_data.updated_item(-1)

                    t1_data.push({'params':{    'laser_wavelength_nm':laser_wavelength,
                                                'laser_power_V'  : laser_power,
                                                'num_points'     : num_points,
                                                'iterations'     : iterations,
                                                'num_samples'    : num_samples,
                                                't_aom_delay_us' : t_aom_delay/1e3,
                                                't_init_us'      : t_init/1e3,
                                                't_readout_delay_min_us'  : t_readout_delay_min/1e3,
                                                't_readout_delay_max_us' : t_readout_delay_max/1e3,
                                                't_readout_us'   : t_readout/1e3,
                                                't_wait_us'      : t_wait/1e3,
                                                'clk_width_us'   : clk_width/1e3,
                                                'record_power'   : record_power, 
                                                'daq_cts_ch'     : daq_cts_channel,
                                                'daq_trig_ch'    : daq_trig_channel,
                                                'daq_clk_ch'     : daq_clk_channel,
                                                'ps_EN_ch'       : ps_EN_channel,
                                                'ps_CTRL_ch'     : ps_CTRL_channel,
                                                'ps_trig_ch'     : ps_trig_channel,
                                                'ps_clk_ch'      : ps_clk_channel,
                                                'ps_aom_ch'      : ps_aom_channel,
                                                'comments'       : comments,
                                                'integrated_counts': int(integrated_counts),},
                                            'title': 'T1',
                                            'xlabel': 'Readout delay time (us)',
                                            'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                            'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                            'ylabel': 'Counts per {t:.3}s'.format(t=t_readout/1e9),
                                            'datasets': {
                                                    'signal' : signal_data,
                                                    'init'   : init_data,
                                                    'power'  : power_data,
                                            }})
                    if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                        # the GUI has asked us nicely to exit
                        return
                    
            print('Done with t1Experiment.')

    def t1PiExperiment(self,
                       dataset,
                       laser_power,
                       mw_power,
                       mw_frequency,
                       t_aom_delay,
                       t_init,
                       t_mw_delay,
                       t_rabi,
                       num_points,
                       iterations,
                       t_readout_delay_min,
                       t_readout_delay_max,
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
                       comments,):
        with MyInstrumentManager() as mgr, DataSource(dataset) as t1Pi_data:
            # Take care of units
            mw_frequency = mw_frequency*1e6 #Hz
            t_aom_delay = t_aom_delay*1e3 #ns
            t_init = t_init*1e3 # ns
            t_mw_delay = t_mw_delay*1e3 #ns
            t_rabi = t_rabi*1e3 #ns
            t_readout_delay_min = t_readout_delay_min*1e3 #ns
            t_readout_delay_max = t_readout_delay_max*1e3 #ns
            t_readout = t_readout*1e3 #ns
            clk_width = t_readout/2

            srs = mgr.srs_driver
            daq = mgr.ni_photonCounting
            pulsestreamer = mgr.pulseStreamer_driver

            signal_data = StreamingList()
            background_data = StreamingList()

            taus = np.linspace(t_readout_delay_min, t_readout_delay_max, num_points)

            # Set starting point of SRS396

            srs.setFreq(mw_frequency)
            srs.setRfAmp(mw_power)
            srs.setRfToggle(1)

            print("Time per point, maximum tau: {t_total:.5}s".format(t_total = (2e-9*(t_init+t_mw_delay+t_rabi+t_readout_delay_max+t_readout+clk_width))))
            for i in range(iterations):
                signal_null = np.empty(num_points)
                signal_null[:] = np.nan
                signal_data.append(np.stack([taus/1e3, signal_null]))
                background_null = np.empty(num_points)
                background_null[:] = np.nan
                background_data.append(np.stack([taus/1e3, background_null]))

                print("Iteration: {iteration}".format(iteration = i+1))

                for t, tau in enumerate(taus):
                    # tau = readout delay (variable)
                    seq = pulsestreamer.ps.createSequence()
                    tau = tau.item() # convert numpy.float64() to Python float object

                    patt0 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+tau+t_readout+t_readout_delay_max-tau+clk_width,0),
                                         (t_init+t_mw_delay+t_rabi+tau+t_readout+t_readout_delay_max-tau+clk_width,0)]

                    patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(t_rabi,1),(tau+t_readout+t_readout_delay_max-tau+clk_width,0),
                                         (t_init+t_mw_delay,0),(t_rabi,0),(tau+t_readout+t_readout_delay_max-tau+clk_width,0)]

                    patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+t_mw_delay+t_rabi+tau+t_readout+t_readout_delay_max-tau-clk_width+clk_width,0),
                                             (clk_width,0),(t_init+t_mw_delay+t_rabi+tau+t_readout+t_readout_delay_max-tau-clk_width+clk_width,0)]

                    patt3 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+tau,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_readout_delay_max-tau,0),
                                         (t_init+t_mw_delay+t_rabi+tau,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_readout_delay_max-tau,0)]

                    patt4 = [(t_init,1),(t_mw_delay+t_rabi+tau,0),(t_readout,1),(t_readout_delay_max-tau+clk_width,0),
                             (t_init,1),(t_mw_delay+t_rabi+tau,0),(t_readout,1),(t_readout_delay_max-tau+clk_width+t_aom_delay,0)]

                    seq.setDigital(ps_EN_channel, patt0)
                    seq.setDigital(ps_CTRL_channel, patt1)
                    seq.setDigital(ps_trig_channel, patt2)
                    seq.setDigital(ps_clk_channel, patt3)
                    seq.setDigital(ps_aom_channel, patt4)


                    pulsestreamer.runSequenceInfinitely(seq)
                    
                    data = daq.readCtrs_singleChannel_externalTrig_externalClk(num_samples*4, daq_cts_channel,
                                                                                                daq_trig_channel,
                                                                                                daq_clk_channel)
                    
                    signal = data[0][0::4]
                    background = data[0][2::4]
                    #print(data)
                    #print(signal)
                    #print(background)

                    signal_data[-1][1][t] = np.sum(signal)
                    background_data[-1][1][t] = np.sum(background)

                    signal_data.updated_item(-1)
                    background_data.updated_item(-1)

                    t1Pi_data.push({'params':{'laser_power_mW' : laser_power,
                                                'mw_power_dBm'   : mw_power,
                                                'mw_frequency_MHz': mw_frequency/1e6,
                                                'num_points'     : num_points,
                                                'iterations'     : iterations,
                                                'num_samples'    : num_samples,
                                                't_aom_delay_us' : t_aom_delay/1e3,
                                                't_init_us'      : t_init/1e3,
                                                't_mw_delay_us'  : t_mw_delay/1e3,
                                                't_rabi_us'      : t_rabi/1e3,
                                                't_readout_delay_min_us'  : t_readout_delay_min/1e3,
                                                't_readout_delay_max_us' : t_readout_delay_max/1e3,
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
                                                'comments'       : comments,},
                                            'title': 'T1 with Pi Pulse',
                                            'xlabel': 'Readout delay time (us)',
                                            'ylabel': 'Counts per {t:.3}s'.format(t=t_readout/1e9),
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
            print('Done with t1PiExperiment.')
