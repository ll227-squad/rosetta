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

class aomDelayExperiment:
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
        _logger.info('Created aomDelayExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed aomDelayExperiment instance.')

    def aomDelayExperiment(self,
                           dataset:str,
                           laser_power,
                           start_aom,
                           photon_read_window,
                           aom_on_window,
                           num_points,
                           avgs_per_point,
                           daq_cts_channel,
                           ps_trig_channel,
                           ps_clk_channel,
                           ps_aom_channel,
                           comments):
        with MyInstrumentManager() as mgr, DataSource(dataset) as aomDelay_data:

            daq = mgr.ni_photonCounting
            pulsestreamer = mgr.pulseStreamer_driver

            signal_data = StreamingList()
            aom_on_time = StreamingList()
            aom_off_time = StreamingList()

            t0 = 0e3
            dt1 = photon_read_window*1e3 #ns
            dt2 = aom_on_window*1e3 #ns
            clk_width = dt1/2
            total = clk_width+dt1+dt1+dt2+dt1+dt1+clk_width
            t1 = clk_width+dt1+dt1

            delays = np.linspace(0,dt1+dt1+dt2-dt1+clk_width+clk_width, num_points)
            signal_null = np.empty(num_points)
            signal_null[:] = np.nan
            signal_data.append(np.stack([delays, signal_null]))
            aom_on_time.append(np.stack([(dt1)*np.ones(len(delays)), np.linspace(0,3000,num_points)])) # when you should start seeing counts IN DELAY FRAME
            aom_off_time.append(np.stack([(dt1+dt1+dt2-dt1)*np.ones(len(delays)), np.linspace(0,3000,num_points)])) # when you should start loosing counts IN DELAY FRAME

            # daq trigger (for convenience)
            patt0 = [(clk_width,1),(total-clk_width,0)]
            # aom
            patt2 = [(clk_width+dt1+dt1,0),(dt2,1),(total-dt2-dt1-dt1-clk_width,0)]


            for d, delay in enumerate(delays):
                print(delay)
                seq = pulsestreamer.ps.createSequence()
                delay = delay.item() # convert numpy.float64 to python float
                # photon read
                patt1 = [(clk_width+delay,0),(clk_width,1),(dt1-clk_width,0),(clk_width,1),(total-clk_width-dt1+clk_width-clk_width-delay-clk_width,0)]
                seq.setDigital(ps_trig_channel, patt0)
                seq.setDigital(ps_clk_channel, patt1)
                seq.setDigital(ps_aom_channel, patt2)
                
                pulsestreamer.runSequenceInfinitely(seq)

                data = daq.readCtrs_singleChannel_externalTrig_externalClk(2*avgs_per_point,daq_cts_channel)
                print(data)
                signal = data[0][0::2]
                signal_data[-1][1][d] = np.average(signal)
                signal_data.updated_item(-1)

                aomDelay_data.push({'params': {'laser_power_mW' : laser_power,
                                            'start_aom'  : start_aom,
                                            'photon_read_window' : photon_read_window,
                                            'aom_on_window' : aom_on_window,
                                            'num_points' : num_points,
                                            'avgs_per_point' : avgs_per_point,
                                            'daq_cts_channel' : daq_cts_channel,
                                            'ps_trig_channel' : ps_trig_channel,
                                            'ps_clk_channel' : ps_clk_channel,
                                            'ps_aom_channel': ps_aom_channel,
                                            'comments'    : comments},
                                    'title' : 'Measure AOM Delay',
                                    'xlabel' : 'Time (ns)',
                                    'ylabel' : 'Counts',
                                    'datasets':{'signal' :signal_data,
                                                'aom_on_time' : aom_on_time,
                                                'aom_off_time' : aom_off_time}})
                
                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    return   
            

            # Shutdown
            mwOFF = pulsestreamer.cwODMRmwOFF(1e9)
            pulsestreamer.runSequenceInfinitely(mwOFF)
            print('Done with aomDelayExperiment.')

if __name__ == '__main__':
    exp = aomDelayExperiment()
    exp.aomDelayExperiment('aomDelay',0,20,10,20, 3, 5,'/Dev1/PFI1',2,3,4,'na')

