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

class signalGeneratorExperiment:
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
        _logger.info('Created signalGeneratorExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed signalGeneratorExperiment instance.')

    def signalGeneratorStatus(self,
                              dataset:str):
            
            """Get the current settings of the signal generator instrument

            Args:
                dataset: name of the dataset to push data to"""
            
            with MyInstrumentManager() as mgr, DataSource(dataset) as signalGenerator_data:
                signalGenerator_driver = mgr.srs_driver

                srsIdentity  = signalGenerator_driver.idn()
                srsFrequency = signalGenerator_driver.getFreq()
                srsAmplitude = signalGenerator_driver.rfAmp()
                srsPhase     = signalGenerator_driver.getPhase()
                srsOnOff     = signalGenerator_driver.rfToggle()
                statusTime   = time.time()

                # save the current data to the data server.
                signalGenerator_data.push({'params': {},
                                'title': 'Signal Generator Status',
                                'datasets': {'identity': srsIdentity,
                                             'frequency': srsFrequency,
                                             'amplitdue': srsAmplitude,
                                             'phase'    : srsPhase,
                                             'on/off?'  : srsOnOff,
                                             'time'     : statusTime}
                })

                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    return
                



    def signalGeneratorFrequencyTrace(self,
                        rate,
                        num_points,
                        dataset:str):
        """Get a time trace of the set point of the SRS 396 Signal generator
        
        Args:
            rate (float): rate in Hz of calls to power meter
            num_points (int): maximum number of data points to collect. If negative, will go infinitely
            dataset: name of the dataset to push data to"""
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as signalGenerator_data:
            signalGenerator_driver = mgr.srs_driver

            self.times = StreamingList()
            self.frequencies = StreamingList()

            self.startTime = time.time()

            # get number of times to sample power meter
            if num_points < 0:
                num_samples = count() # infinite iterator
            else:
                num_samples = range(int(num_points))

            # main experiment loop
            for i in num_samples:
                current_time = time.time()-self.startTime
                current_frequency = signalGenerator_driver.getFreq()
                
                self.times.append(current_time)
                self.frequencies.append(current_frequency)
                print(current_frequency)
                time.sleep(1/rate)


                # save the current data to the data server
                signalGenerator_data.push({'params':{'rate':rate,'num_points':num_points},
                                     'title': 'Signal generator frequency, time trace',
                                     'xlabel': 'Time (s)',
                                     'ylabel': "Frequency (Hz)",
                                     'datasets':{'times'      : self.times,
                                                 'frequencies': self.frequencies}
                                     })

                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    return     


if __name__ == '__main__':
    exp = signalGeneratorExperiment()
    exp.signalGeneratorStatus('signalGeneratorStatus')