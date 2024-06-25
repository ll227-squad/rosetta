import time
import logging
from pathlib import Path
from itertools import count

from nspyre import DataSource
from nspyre import InstrumentGateway
from nspyre import nspyre_init_logger
from nspyre import experiment_widget_process_queue
from nspyre import StreamingList

from rpyc.utils.classic import obtain

from rosetta.insmgr import MyInstrumentManager

_HERE = Path(__file__).parent
_logger = logging.getLogger(__name__)

class cwaveExperiment:
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
        _logger.info('Created cwaveExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed cwaveExperiment instance.')

    def cwaveTrace(self,
                   rate,
                   num_points,
                   dataset:str):
        """Get a time trace of reading a power meter instrument
        
        Args:
            rate (float): rate in Hz of calls to power meter
            num_points (int): maximum number of data points to collect. If negative, will go infinitely
            dataset: name of the dataset to push data to"""
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as cwave_data:
            cwave_driver = mgr.cwave_driver

            cwave_driver.connect('192.168.1.10')

            self.times      = StreamingList()
            self.powers_OPO = StreamingList()
            self.powers_SHG = StreamingList()
            self.powers_PMP = StreamingList()

            self.startTime = time.time()

            # get number of times to sample power meter
            if num_points < 0:
                num_samples = count() # infinite iterator
            else:
                num_samples = range(int(num_points))

            # main experiment loop
            for i in num_samples:
                current_time = time.time()-self.startTime
                current_power_OPO = cwave_driver.get_status().pdOpoPower
                current_power_SHG = cwave_driver.get_status().pdShgPower
                current_power_PMP = cwave_driver.get_status().pdPumpPower
                
                self.times.append(current_time)
                self.powers_OPO.append(current_power_OPO)
                self.powers_SHG.append(current_power_SHG)
                self.powers_PMP.append(current_power_PMP)

                #print(current_power_OPO)
                print(current_power_SHG)
                print(current_power_PMP)
                time.sleep(1/rate)


                # save the current data to the data server
                cwave_data.push({'params':{'rate':rate,'num_points':num_points},
                                     'title': 'C-WAVE power vs time trace',
                                     'xlabel': 'Time (s)',
                                     'ylabel': "Power",
                                     'datasets':{'times'          : self.times,
                                                 'OPO powers'     : self.powers_OPO,
                                                 'SHG powers'     : self.powers_SHG,
                                                 'Pump powers'    : self.powers_PMP}
                                     })

                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    return     


if __name__ == '__main__':
    exp = cwaveExperiment()
    exp.cwaveTrace(1,10,'cwaveTrace')