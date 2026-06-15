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

class t2RamseyExperiment:
    " Different flavors of T2 Ramsey"
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
        _logger.info('Created t2RamseyExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed t2RamseyExperiment instance.')

    def t2RamseyExperiment(self,
                           dataset:str,
                           laser_power,
                           mw_power,
                           mw_frequency,
                           t_aom_delay,
                           t_init,
                           t_mw_delay,
                           t_pi2,
                           t_delay_min,
                           t_delay_max,
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
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as t2Ramsey_data:
                # Take care of units
                mw_frequency = mw_frequency*1e6 #Hz
                t_aom_delay = t_aom_delay*1e3 #ns
                t_init = t_init*1e3 # ns
                t_mw_delay = t_mw_delay*1e3 #ns
                t_pi2 = t_pi2*1e3 #ns
                t_delay_min = t_delay_min*1e3 #ns
                t_delay_max = t_delay_max*1e3 #ns
                t_readout_delay = t_readout_delay*1e3 #ns
                t_readout = t_readout*1e3 #ns
                clk_width = t_readout/2

                agilent        = mgr.e8257d_driver2 #MW sig gen
                daq = mgr.ni_photonCounting
                pulsestreamer = mgr.pulseStreamer_driver

                signal_data = StreamingList()
                background_data = StreamingList()

                taus = np.linspace(t_delay_min, t_delay_max, num_points)

                # Set starting point of SRS396

                # Set starting point of SRS396
                agilent.set_rf_freq(mw_frequency)
                print('Set SRS396 frequency to {freq:.6f} MHz.'.format(freq = mw_frequency/1e6))
                agilent.set_rf_amp(mw_power)
                print('Set SRS396 output amplitude to {amp:.2f} dBm.'.format(amp= mw_power))
                agilent.set_rf_toggle(1)
                print('Turn on RF output of SRS396.')

                print("Time per point, maximum tau: {t_total:.5}s".format(t_total = (2e-9*(t_init+t_mw_delay+t_pi2+t_delay_max+t_pi2+t_readout_delay+t_readout+t_delay_max-t_delay_max))))
                for i in range(iterations):
                    signal_null = np.empty(num_points)
                    signal_null[:] = np.nan
                    signal_data.append(np.stack([taus/1e3, signal_null]))
                    background_null = np.empty(num_points)
                    background_null[:] = np.nan
                    background_data.append(np.stack([taus/1e3, background_null]))

                    print("Iteration: {iteration}".format(iteration = i+1))

                    for t, tau in enumerate(taus):
                        #rabiSeq = pulsestreamer.rabi_diff(t_init, t_mw_delay, tau, t_readout_delay, t_readout, t_rabi_max, clk_width, clk_buffer)
                        seq = pulsestreamer.ps.createSequence()
                        tau = tau.item() # convert numpy.float64() to Python float object

                        patt0 = [(t_aom_delay+t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_delay_max-tau+clk_width,0),
                                             (t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_delay_max-tau+clk_width,0)]

                        patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(t_pi2,1),(tau,0),(t_pi2,1),(t_readout_delay+t_readout+t_delay_max-tau+clk_width,0),
                                             (t_init+t_mw_delay,0),(t_pi2,1),(tau,0),(t_pi2,1),(t_readout_delay+t_readout+t_delay_max-tau+clk_width,0)]

                        patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+t_mw_delay+t_pi2+tau+t_pi2+t_readout_delay+t_readout+t_delay_max-tau-clk_width+clk_width,0),
                                                 (clk_width,0),(t_init+t_mw_delay+t_pi2+tau+t_pi2+t_readout_delay+t_readout+t_delay_max-tau-clk_width+clk_width,0)]

                        patt3 = [(t_aom_delay+t_init+t_mw_delay+t_pi2+tau+t_pi2+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_delay_max-tau,0),
                                             (t_init+t_mw_delay+t_pi2+tau+t_pi2+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_delay_max-tau,0)]

                        patt4 = [(t_init,1),(t_mw_delay+t_pi2+tau+t_pi2+t_readout_delay,0),(t_readout,1),(t_delay_max-tau+clk_width,0),
                                 (t_init,1),(t_mw_delay+t_pi2+tau+t_pi2+t_readout_delay,0),(t_readout,1),(t_delay_max-tau+clk_width+t_aom_delay,0)]
                        
                        pattA1 = [(t_init,1),(t_mw_delay+t_pi2+tau+t_pi2+t_readout_delay,0),(t_readout,1),(t_delay_max-tau+clk_width,0),
                                 (t_init,1),(t_mw_delay+t_pi2+tau+t_pi2+t_readout_delay,0),(t_readout,1),(t_delay_max-tau+clk_width+t_aom_delay,0)]

                        seq.setDigital(ps_EN_channel, patt0)
                        seq.setDigital(ps_CTRL_channel, patt1)
                        seq.setDigital(ps_trig_channel, patt2)
                        seq.setDigital(ps_clk_channel, patt3)
                        seq.setDigital(ps_aom_channel, patt4)
                        seq.setAnalog(ps_aomAnalog_channel, pattA1)


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

                        t2Ramsey_data.push({'params':{'laser_power_mW' : laser_power,
                                                    'mw_power_dBm'   : mw_power,
                                                    'mw_frequency_MHz': mw_frequency/1e6,
                                                    'num_points'     : num_points,
                                                    'iterations'     : iterations,
                                                    'num_samples'    : num_samples,
                                                    't_aom_delay_us' : t_aom_delay/1e3,
                                                    't_init_us'      : t_init/1e3,
                                                    't_mw_delay_us'  : t_mw_delay/1e3,
                                                    't_pi2_us'       : t_pi2/1e3,
                                                    't_delay_min_us'  : t_delay_min/1e3,
                                                    't_delay_max_us'  : t_delay_max/1e3,
                                                    't_readout_delay_us' : t_readout_delay/1e3,
                                                    't_readout_us'   : t_readout/1e3,
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
                                                'title': 'T2 Ramsey',
                                                'xlabel': 'Ramsey delay time (us)',
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
                agilent.set_rf_toggle(0)
                print('Done with t2RamseyExperiment.')