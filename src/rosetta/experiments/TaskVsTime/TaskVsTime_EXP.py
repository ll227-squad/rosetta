import time
import logging
from pathlib import Path
from itertools import count

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

    def taskVsTimeMeasurement(self, rate: float, num_points: int, autosave: bool, autosave_interval: int, dataset:str, **kwargs):
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as taskVsTime_data:
            daq = mgr.ni_photonCounting

            # storage for experiment data
            self.times = StreamingList()
            self.pfi11counts = StreamingList()
            #self.pfi4counts  = StreamingList()
            self.pfi1counts  = StreamingList()

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

                current_counts = daq.readCtrs_single_internalClk(acqRate=rate)
                for data, countsList in zip(current_counts,self.dataCounts):
                    countsList.append(data)

                self.times.append(time.time()-self.startTime)

                # save the current data to the data server
                taskVsTime_data.push({'params'  :{'Dataset Name' :dataset,
                                                  'Sampling Rate':rate,
                                                  'Number of Points':num_points},
                                      'title'   : 'Task vs Time',
                                      'xlabel'  : 'Time (s)',
                                      'ylabel'  : 'Counts',
                                      'datasets':{'times'      :self.times,
                                                  'pfi11counts':self.pfi11counts,
                                                  'pfi1counts' :self.pfi1counts}
                                    })
                
                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    return    

if __name__ == '__main__':
    exp = taskVsTimeExperiment()
    exp.taskVsTimeMeasurement(1, 1, False, 1, 'taskVsTimeMeasurement')