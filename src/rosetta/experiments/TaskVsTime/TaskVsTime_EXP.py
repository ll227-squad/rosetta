import time
import logging
from pathlib import Path
from itertools import count
import numpy as np
from scipy import signal

from nspyre import nspyre_init_logger
from nspyre import StreamingList, DataSource, experiment_widget_process_queue

from rosetta.drivers.ni.ni_photonCounting import nidaqPhotonCounter
from rosetta.insmgr import MyInstrumentManager

_HERE = Path(__file__).parent
_logger = logging.getLogger(__name__)


class taskVsTimeExperiment:

    def __init__(self, queue_to_exp=None, queue_from_exp=None):
        """
        Args:
            queue_to_exp: A multiprocessing Queue object used to send messages
                to the experiment from the GUI.
            queue_from_exp: A multiprocessing Queue object used to send messages
                to the GUI from the experiment.
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
        _logger.info('Created taskVsTimeExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed taskVsTimeExperiment instance.')

    def taskVsTimeMeasurement(self, rate: float, num_points: int, record_power: bool, laser_wavelength: float, autosave: bool, autosave_interval: int, dataset:str, **kwargs):
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as taskVsTime_data:
            daq = mgr.ni_photonCounting
            if record_power==True:
                pm  = mgr.powerMeter_driver
                pm.set_correction_wavelength(laser_wavelength) # send as nm

            # storage for experiment data
            self.times = StreamingList()
            self.pfi11counts = StreamingList()
            #self.pfi4counts  = StreamingList()
            self.pfi1counts  = StreamingList()
            self.optical_powers = StreamingList()

            self.dataCounts = [self.pfi11counts, self.pfi1counts]


            # get start time
            self.startTime = time.time()

            # get number of times to sample power meter
            if num_points < 0:
                num_samples = count() # infinite iterator
            else:
                num_samples = range(int(num_points))

            # main experiment loop
            for i in num_samples:
                current_time = time.time()-self.startTime
                if record_power==True:
                    current_optical_power = pm.get_power() * 1e3 #mW
                else:
                    current_optical_power = 1.0

                current_counts = daq.readCtrs_single_internalClk(acqRate=rate)
                current_rates = [counts * rate for counts in current_counts]
                for data, countsList in zip(current_rates,self.dataCounts):
                    countsList.append(data)

                self.times.append(time.time()-self.startTime)
                self.optical_powers.append(current_optical_power)

                # save the current data to the data server
                taskVsTime_data.push({'params'  :{'Dataset Name' :dataset,
                                                  'Sampling Rate':rate,
                                                  'Number of Points':num_points,},
                                      'title'   : 'Task vs Time',
                                      'xlabel'  : 'Time (s)',
                                      'ylabel'  : 'Counts',
                                      'datasets':{'times'      :self.times,
                                                  'pfi11counts':self.pfi11counts,
                                                  'pfi1counts' :self.pfi1counts,
                                                  'optical_powers_mW': self.optical_powers,}
                                    })
                
                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    return    
                
    def aoaiVsTimeMeasurement(self, dataset:str, rate:float, num_points:int, V_pp:float, ao_channel, ai_channel):
        with MyInstrumentManager() as mgr, DataSource(dataset) as aoaiVsTime_data:
            daq = mgr.ni_analogTasks
            pm  = mgr.powerMeter_driver

            # storage for experiment data
            times = StreamingList()
            optical_powers = StreamingList()
            ao_values = StreamingList()
            #self.pfi4counts  = StreamingList()
            ai_values  = StreamingList()
            timeai_values = StreamingList()

            # get start time
            startTime = time.time()

            # triangle wave
            t = np.linspace(0,1/rate, int(num_points))
            x = V_pp/2*signal.sawtooth(2 * np.pi * rate * t)+ V_pp/2

            # get number of times to sample power meter
            if num_points < 0:
                num_samples = count() # infinite iterator
            else:
                num_samples = range(int(num_points))

            for i in num_samples:
                current_time = time.time()-startTime
                daq.writeAO(ao_channel, x[int(i % num_points)])
                time.sleep(0.1/rate)
                data = daq.readAI(ai_channel)
                time.sleep(0.5/rate)

                times.append(current_time)
                ao_values.append(x[int(i % num_points)])
                ai_values.append(data)

                timeai_values.append(np.stack([x[int(i % num_points)], data]))
                # np array of [[t1,t2,t3],[s1,s2,s3]]

                # save the current data to the data server
                aoaiVsTime_data.push({'params'  :{'Dataset Name' :dataset,
                                                  'Sampling Rate':rate,
                                                  'Number of Points':num_points,
                                                  'Vpp' : V_pp,
                                                  'AO Channel': ao_channel,
                                                  'AI Channel': ai_channel},

                                      'title'   : 'AI vs AO',
                                      'xlabel'  : 'Time (s)',
                                      'ylabel'  : 'AI Voltage (V)',
                                      'datasets':{'times'     :times,
                                                  'ao_values' :ao_values,
                                                  'ai_values' :ai_values,
                                                  'timeai_values': timeai_values}
                                    })
                
                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    return   
                
            daq.writeAO(ao_channel,0)




if __name__ == '__main__':
    exp = taskVsTimeExperiment()
    exp.aoaiVsTimeMeasurement('aoaivstime', 10, 100, 1, 'Dev1/AO2', 'Dev1/AI4')