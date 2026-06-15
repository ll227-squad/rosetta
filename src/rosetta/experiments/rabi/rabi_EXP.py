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

class rabiExperiment:
    " Different flavors of Rabi"
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
        _logger.info('Created rabiExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed rabiExperiment instance.')

    def rabiDiffExperiment(self,
                           dataset:str,
                           laser_power,
                           mw_power,
                           mw_frequency,
                           t_aom_delay,
                           t_init,
                           t_mw_delay,
                           t_rabi_min,
                           t_rabi_max,
                           num_points,
                           iterations,
                           t_readout_delay,
                           t_readout,
                           num_samples,
                           clk_width,
                           clk_buffer,
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
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as rabiDiff_data:
                # Take care of units
                mw_frequency = mw_frequency*1e6 #Hz
                t_aom_delay = t_aom_delay*1e3 #ns
                t_init = t_init*1e3 # ns
                t_mw_delay = t_mw_delay*1e3 #ns
                t_rabi_min = t_rabi_min*1e3 #ns
                t_rabi_max = t_rabi_max*1e3 #ns
                t_readout_delay = t_readout_delay*1e3 #ns
                t_readout = t_readout*1e3 #ns
                clk_width = t_readout/2

                srs = mgr.srs_driver
                agilent2 = mgr.e8257d_driver2
                daq = mgr.ni_photonCounting
                schottky_diode = mgr.ni_analogTasks
                pulsestreamer = mgr.pulseStreamer_driver

                times = StreamingList()
                signal_data = StreamingList()
                background_data = StreamingList()
                schottky_data = StreamingList()

                taus = np.linspace(t_rabi_min, t_rabi_max, num_points)

                # Set starting point of SRS396
                #srs.setFreq(mw_frequency)
                #srs.setRfAmp(mw_power)
                #srs.setRfToggle(1)

                # Set starting point of Agilent E8257D #2 (MW cycling one)
                agilent2.set_rf_freq(mw_frequency)
                print('Set E8257D #2 frequency to {freq:.6f} MHz.'.format(freq = mw_frequency/1e6))
                agilent2.set_rf_amp(mw_power)
                print('Set E8257D #2 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
                agilent2.set_rf_toggle(1)
                print('Turn on RF output of E8257D #2.')

                print("Time per point, maximum tau: {t_total:.5}s".format(t_total = (2e-9*(t_init+t_mw_delay+t_rabi_max+t_readout_delay+t_readout+t_rabi_max-t_rabi_max))))
                for i in range(iterations):
                    signal_null = np.empty(num_points)
                    signal_null[:] = np.nan
                    signal_data.append(np.stack([taus/1e3, signal_null]))
                    background_null = np.empty(num_points)
                    background_null[:] = np.nan
                    background_data.append(np.stack([taus/1e3, background_null]))
                    schottky_null = np.empty(num_points)
                    schottky_null[:] = np.nan
                    schottky_data.append(np.stack([taus/1e3, schottky_null]))

                    print("Iteration: {iteration}".format(iteration = i+1))

                    for t, tau in enumerate(taus):
                        #rabiSeq = pulsestreamer.rabi_diff(t_init, t_mw_delay, tau, t_readout_delay, t_readout, t_rabi_max, clk_width, clk_buffer)
                        rabiSeq = pulsestreamer.ps.createSequence()
                        tau = tau.item() # convert numpy.float64() to Python float object

                        patt0 = [(t_aom_delay+t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau+clk_width,0),
                                             (t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau+clk_width,0)]

                        patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(tau,1),(t_readout_delay+t_readout+t_rabi_max-tau+clk_width,0),
                                             (t_init+t_mw_delay,0),(tau,0),(t_readout_delay+t_readout+t_rabi_max-tau+clk_width,0)]

                        patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau-clk_width+clk_width,0),
                                                 (clk_width,0),(t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau-clk_width+clk_width,0)]

                        patt3 = [(t_aom_delay+t_init+t_mw_delay+tau+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_rabi_max-tau,0),
                                             (t_init+t_mw_delay+tau+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_rabi_max-tau,0)]

                        patt4 = [(t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_readout,1),(t_rabi_max-tau+clk_width,0),
                                 (t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_readout,1),(t_rabi_max-tau+clk_width+t_aom_delay,0)]
                        
                        pattA1= [(t_init,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_readout,laser_power),(t_rabi_max-tau+clk_width,0.0),
                                 (t_init,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_readout,laser_power),(t_rabi_max-tau+clk_width+t_aom_delay,0.0)]

                        rabiSeq.setDigital(ps_EN_channel, patt0)
                        rabiSeq.setDigital(ps_CTRL_channel, patt1)
                        rabiSeq.setDigital(ps_trig_channel, patt2)
                        rabiSeq.setDigital(ps_clk_channel, patt3)
                        rabiSeq.setDigital(ps_aom_channel, patt4)
                        rabiSeq.setAnalog(ps_aomAnalog_channel, pattA1)


                        pulsestreamer.runSequenceInfinitely(rabiSeq)

                        time.sleep(10e-3)
                        
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

                        rabiDiff_data.push({'params':{'laser_power_V' : laser_power,
                                                    'mw_power_dBm'   : mw_power,
                                                    'mw_frequency_MHz': mw_frequency/1e6,
                                                    'num_points'     : num_points,
                                                    'iterations'     : iterations,
                                                    'num_samples'    : num_samples,
                                                    't_aom_delay_us' : t_aom_delay/1e3,
                                                    't_init_us'      : t_init/1e3,
                                                    't_mw_delay_us'  : t_mw_delay/1e3,
                                                    't_rabi_min_us'  : t_rabi_min/1e3,
                                                    't_rabi_max_us'  : t_rabi_max/1e3,
                                                    't_readout_delay_us' : t_readout_delay/1e3,
                                                    't_readout_us'   : t_readout/1e3,
                                                    'clk_width_us'   : clk_width/1e3,
                                                    'clk_buffer_us'  : clk_buffer/1e3,
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
                                                'title': 'Rabi',
                                                'xlabel': 'Rabi pulse length (us)',
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
                print('Done with rabiDiffExperiment.')

    def rabiAbbrExperiment(self,
                           dataset:str,
                           laser_power,
                           mw_power,
                           mw_frequency,
                           t_aom_delay,
                           t_init,
                           t_mw_delay,
                           t_rabi_min,
                           t_rabi_max,
                           num_points,
                           iterations,
                           t_readout_delay,
                           t_readout,
                           num_samples,
                           clk_width,
                           clk_buffer,
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
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as rabiAbbr_data:
                # Take care of units
                mw_frequency = mw_frequency*1e6 #Hz
                t_aom_delay = t_aom_delay*1e3 #ns
                t_init = t_init*1e3 # ns
                t_mw_delay = t_mw_delay*1e3 #ns
                t_rabi_min = t_rabi_min*1e3 #ns
                t_rabi_max = t_rabi_max*1e3 #ns
                t_readout_delay = t_readout_delay*1e3 #ns
                t_readout = t_readout*1e3 #ns
                clk_width = t_readout/10
                clk_buffer = clk_buffer*1e3 #ns

                srs = mgr.srs_driver
                agilent2 = mgr.e8257d_driver2
                daq = mgr.ni_photonCounting
                schottky_diode = mgr.ni_analogTasks
                pulsestreamer = mgr.pulseStreamer_driver

                times = StreamingList()
                signal_data = StreamingList()
                background_data = StreamingList()
                schottky_data = StreamingList()

                taus = np.linspace(t_rabi_min, t_rabi_max, num_points)

                # Set starting point of SRS396
                #srs.setFreq(mw_frequency)
                #srs.setRfAmp(mw_power)
                #srs.setRfToggle(1)

                # Set starting point of Agilent E8257D #2 (MW cycling one)
                agilent2.set_rf_freq(mw_frequency)
                print('Set E8257D #2 frequency to {freq:.6f} MHz.'.format(freq = mw_frequency/1e6))
                agilent2.set_rf_amp(mw_power)
                print('Set E8257D #2 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
                agilent2.set_rf_toggle(1)
                print('Turn on RF output of E8257D #2.')

                print("Time per point: {t_total:.5}s".format(t_total = (1e-9*(t_init+t_mw_delay+t_readout_delay+t_init+t_rabi_max+t_aom_delay))))
                for i in range(iterations):
                    signal_null = np.empty(num_points)
                    signal_null[:] = np.nan
                    signal_data.append(np.stack([taus/1e3, signal_null]))
                    background_null = np.empty(num_points)
                    background_null[:] = np.nan
                    background_data.append(np.stack([taus/1e3, background_null]))
                    schottky_null = np.empty(num_points)
                    schottky_null[:] = np.nan
                    schottky_data.append(np.stack([taus/1e3, schottky_null]))

                    print("Iteration: {iteration}".format(iteration = i+1))

                    for t, tau in enumerate(taus):
                        #rabiSeq = pulsestreamer.rabi_diff(t_init, t_mw_delay, tau, t_readout_delay, t_readout, t_rabi_max, clk_width, clk_buffer)
                        rabiSeq = pulsestreamer.ps.createSequence()
                        tau = tau.item() # convert numpy.float64() to Python float object

                        patt0 = [(t_aom_delay+t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau,0)]

                        patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(tau,1),(t_readout_delay+t_init+t_rabi_max-tau,0)]

                        patt2 = [(t_aom_delay,0),(clk_width,1),(t_init-clk_width+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau,0)]

                        patt3 = [(t_aom_delay+t_init-t_readout,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_mw_delay+tau+t_readout_delay-clk_width+clk_buffer,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-clk_buffer+t_readout-clk_width+t_rabi_max-tau,0)]

                        patt4 = [            (t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_init+t_rabi_max-tau+t_aom_delay,1)]

                        patt5 = [(t_aom_delay+t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau,0)]
                        
                        pattA1= [            (t_init,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_init+t_rabi_max-tau+t_aom_delay,laser_power)]

                        rabiSeq.setDigital(ps_EN_channel, patt0)
                        rabiSeq.setDigital(ps_CTRL_channel, patt1)
                        rabiSeq.setDigital(ps_trig_channel, patt2)
                        rabiSeq.setDigital(ps_clk_channel, patt3)
                        rabiSeq.setDigital(ps_aom_channel, patt4)
                        rabiSeq.setDigital(5, patt5)
                        rabiSeq.setAnalog(ps_aomAnalog_channel, pattA1)


                        pulsestreamer.runSequenceInfinitely(rabiSeq)
                        
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

                        rabiAbbr_data.push({'params':{'laser_power_V' : laser_power,
                                                    'mw_power_dBm'   : mw_power,
                                                    'mw_frequency_MHz': mw_frequency/1e6,
                                                    'num_points'     : num_points,
                                                    'iterations'     : iterations,
                                                    'num_samples'    : num_samples,
                                                    't_aom_delay_us' : t_aom_delay/1e3,
                                                    't_init_us'      : t_init/1e3,
                                                    't_mw_delay_us'  : t_mw_delay/1e3,
                                                    't_rabi_min_us'  : t_rabi_min/1e3,
                                                    't_rabi_max_us'  : t_rabi_max/1e3,
                                                    't_readout_delay_us' : t_readout_delay/1e3,
                                                    't_readout_us'   : t_readout/1e3,
                                                    'clk_width_us'   : clk_width/1e3,
                                                    'clk_buffer_us'  : clk_buffer/1e3,
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
                                                'title': 'Rabi',
                                                'xlabel': 'Rabi pulse length (us)',
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
                print('Done with rabiAbbrExperiment.')

    def rabi_test(self,
                           dataset:str,
                           laser_power,
                           mw_power,
                           mw_frequency,
                           t_init,
                           t_mw_delay,
                           t_rabi_min,
                           t_rabi_max,
                           num_points,
                           iterations,
                           t_readout_delay,
                           t_readout,
                           num_samples,
                           clk_width,
                           clk_buffer,
                           daq_cts_channel,
                           daq_trig_channel,
                           daq_clk_channel,
                           ps_EN_channel,
                           ps_CTRL_channel,
                           ps_trig_channel,
                           ps_clk_channel,
                           ps_aom_channel,
                           comments,):
            with MyInstrumentManager() as mgr, DataSource(dataset) as rabiDiff_data:    
                mw_frequency = mw_frequency*1e6 #Hz
                t_init = t_init*1e3 # ns
                t_mw_delay = t_mw_delay*1e3 #ns
                t_rabi_min = t_rabi_min*1e3 #ns
                t_rabi_max = t_rabi_max*1e3 #ns
                t_readout_delay = t_readout_delay*1e3 #ns
                t_readout = t_readout*1e3 #ns
                clk_width = clk_width*1e3 #ns
                clk_buffer = clk_buffer*1e3 #ns
                tau = t_rabi_min

                pulsestreamer = mgr.pulseStreamer_driver
                rabiSeq = pulsestreamer.ps.createSequence()

                patt0 = [(2*(t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau), 0)]
                patt1 = [(t_init+t_mw_delay, 0),
                        (tau, 1),
                        (t_readout_delay+t_readout+t_rabi_max-tau+t_init+t_mw_delay, 0),
                        (tau, 0),
                        (t_readout_delay+t_readout+t_rabi_max-tau, 0)]
                patt4 = [(t_init, 1),
                        (t_mw_delay+tau+t_readout_delay, 0),
                        (t_readout, 1),
                        (t_rabi_max-tau, 0),
                        (t_init, 1),
                        (t_mw_delay+tau+t_readout_delay, 0),
                        (t_readout, 1),
                        (t_rabi_max-tau, 0)]
                patt2 = [(clk_buffer, 0),
                        (clk_width, 1),
                        (t_init-clk_buffer-clk_width+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau+t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau, 0)]
                patt3 = [(t_init+t_mw_delay+tau+t_readout_delay+clk_buffer, 0),
                        (clk_width, 1),
                        (t_readout-clk_width-clk_buffer-clk_buffer, 0),
                        (clk_width, 1),
                        (clk_buffer + t_rabi_max-tau+t_init+t_mw_delay+tau+t_readout_delay+clk_buffer, 0),
                        (clk_width, 1),
                        (t_readout-clk_width-clk_buffer-clk_buffer,0),
                        (clk_width, 1),
                        (clk_buffer+t_rabi_max-tau, 0)]


                #rabiSeq.setDigital(ps_EN_channel, patt0)
                #rabiSeq.setDigital(ps_CTRL_channel, patt1)
                rabiSeq.setDigital(ps_trig_channel, patt2)
                rabiSeq.setDigital(ps_clk_channel, patt3)
                #rabiSeq.setDigital(ps_aom_channel, patt4)

                pulsestreamer.runSequenceInfinitely(rabiSeq)
        

if __name__ == '__main__':
    exp = rabiExperiment()
    """
    exp.rabiDiffExperiment(dataset='rabiDiff',
                           laser_power=1,
                           mw_power=-50,
                           mw_frequency=1355,
                           t_init=500, #us
                           t_mw_delay=100, #us
                           t_rabi_min=500, #us
                           t_rabi_max=600, #us
                           num_points = 2, # how many taus
                           iterations =1, # how many times to repeat measurement at each tau
                           t_readout_delay = 100, #us
                           t_readout = 500, #us
                           num_samples = 5, # how many averages to perform at each tau in one iteration
                           clk_width = 10, #us, width of clk pulses--keep constant 
                           clk_buffer = 10, #us, buffer on each side of t_readout where clk is pushed inside readout window
                           daq_cts_channel = "/Dev1/PFI1",
                           daq_trig_channel = "/Dev1/PFI2",
                           daq_clk_channel = "/Dev1/PFI3",
                           ps_EN_channel = 0,
                           ps_CTRL_channel = 1,
                           ps_trig_channel = 2,
                           ps_clk_channel = 3,
                           ps_aom_channel = 4,
                           comments = 'none')
    """
    exp.rabiDiffExperiment(dataset='rabiDiff',
                           laser_power=1,
                           mw_power=-50,
                           mw_frequency=1352.6,
                           t_aom_delay=1.1, #us
                           t_init=1000, #us
                           t_mw_delay=1, #us
                           t_rabi_min=0.005, #us
                           t_rabi_max=0.055, #us
                           num_points = 6, # how many taus
                           iterations =2, # how many times to repeat measurement at each tau
                           t_readout_delay = 1, #us
                           t_readout = 50, #us
                           num_samples = 10, # how many averages to perform at each tau in one iteration
                           clk_width = 5, #us, width of clk pulses--keep constant 
                           clk_buffer = 1, #us, buffer on each side of t_readout where clk is pushed inside readout window
                           daq_cts_channel = "/Dev1/PFI1",
                           daq_trig_channel = "/Dev1/PFI2",
                           daq_clk_channel = "/Dev1/PFI3",
                           ps_EN_channel = 0,
                           ps_CTRL_channel = 1,
                           ps_trig_channel = 2,
                           ps_clk_channel = 3,
                           ps_aom_channel = 4,
                           comments = 'none')
    """
    exp.rabi_test('test',1,-50,1355,100,100,100,200,5,1,100,100,5,50,1,"/Dev1/PFI1",
                           "/Dev1/PFI2",
                           "/Dev1/PFI3",
                           0,
                           1,
                           2,
                           3,
                           4,
                           'none')
    """