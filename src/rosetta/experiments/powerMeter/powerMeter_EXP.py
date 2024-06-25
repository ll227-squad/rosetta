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

class powerMeterExperiment:
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
        _logger.info('Created powerMeterExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed powerMeterExperiment instance.')

    def powerMeterMeasurement(self,
                              dataset:str):
        
        """Get the power reading of a power meter instrument

        Args:
            dataset: name of the dataset to push data to"""
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as powerMeter_data:
            powerMeter_driver = mgr.powerMeter_driver

            powerReading = powerMeter_driver.get_power()
            powerUnits = powerMeter_driver.get_units()

            # save the current data to the data server.
            powerMeter_data.push({'params': {},
                            'title': 'Power Meter single reading',
                            'units': powerUnits,
                            'datasets': {'power' : powerReading}
            })

            if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                # the GUI has asked us nicely to exit
                return
            
    def powerMeterTrace(self,
                        rate,
                        num_points,
                        dataset:str):
        """Get a time trace of reading a power meter instrument
        
        Args:
            rate (float): rate in Hz of calls to power meter
            num_points (int): maximum number of data points to collect. If negative, will go infinitely
            dataset: name of the dataset to push data to"""
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as powerMeter_data:
            powerMeter_driver = mgr.powerMeter_driver

            self.times = StreamingList()
            self.powers = StreamingList()

            self.startTime = time.time()
            self.units = powerMeter_driver.get_units()

            # get number of times to sample power meter
            if num_points < 0:
                num_samples = count() # infinite iterator
            else:
                num_samples = range(int(num_points))

            # main experiment loop
            for i in num_samples:
                current_time = time.time()-self.startTime
                current_power = powerMeter_driver.get_power()
                
                self.times.append(current_time)
                self.powers.append(current_power)
                print(current_power)
                time.sleep(1/rate)


                # save the current data to the data server
                powerMeter_data.push({'params':{'rate':rate,'num_points':num_points},
                                     'title': 'Power meter time trace',
                                     'xlabel': 'Time (s)',
                                     'ylabel': "Power",
                                     'units': self.units,
                                     'datasets':{'times'      : self.times,
                                                 'powers'     : self.powers}
                                     })

                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    return     


if __name__ == '__main__':
    exp = powerMeterExperiment()
    exp.powerMeterMeasurement('powerMeasurement')

