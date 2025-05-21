import time
import logging
import enum
from pathlib import Path
from itertools import count

from nspyre import DataSource
from nspyre import InstrumentGateway
from nspyre import nspyre_init_logger
from nspyre import experiment_widget_process_queue
from nspyre import StreamingList

from rpyc.utils.classic import obtain

from rosetta.insmgr import MyInstrumentManager

from rosetta.drivers.hubner import gtr

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

            cwave_driver.connect('192.168.202.10')

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
                #print(current_power_SHG)
                #print(current_power_PMP)
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

    def cwavePLE(self, dataset:str, min_piezo:float, max_piezo:float, scan_rate:float,
                                    num_points:int, measure_rate:float,
                                    data_channel:str, ctr_channel:str, sampling_rate:float):
        """
        Get counts on DAQ chanel PFI as as the C-WAVE's OPO piezo sweeps through min_piezo (e.g. 10% of piezo range) and max_piezo (90% of piezo range).

        Manually set C-WAVE to center wavelength. Put Lyot filter into inselective position manually if necessary.
        
        Repeat num_points:
        [ At t0: record t_initial, wl_initial, p_initial
          Record number of counts on PFI channel for 1/measure_rate time
          At t1: record t_final, wl_final, p_final
          Calculate t_average, wl_average, p_average
          Push data to dataserv, with the intent to plot (counts vs wls_average) where counts may be nomalized by ps_average ]

        Args:
            dataset: name of the dataset to push data to
            min_piezo: Between 0% and 100% (kindly stay away from extremes, so realistically, between 5% and 95%) of C-WAVE's OPO piezo scan range
            max_piezo: Between 0% and 100% (kindly stay away from extremes, so realistically, between 5% and 95%) of C-WAVE's OPO piezo scan range
            scan_rate (Hz): Rate at which OPO piezo sweeps through min_piezo and max_piezo
            num_points (int): Number of points to take in PLE scan
            measure_rate (Hz): Length of time that DAQ is asked to read data_channel; should be about 10x higher than scan_rate to prevent aliasing
            data_channel: e.g. Dev1/PFI1
            ctr_channel: e.g. Dev1/ctr0
            sampling_rate (Hz): Rate at which counts on data_channel are read from DAQ
        """
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as cwavePLE_data:
            # Instantiate and connect to instruments
            cwave = mgr.cwave_driver
            cwave.connect('192.168.202.10')

            daq = mgr.ni_photonCounting

            #wlm = mgr.WS8_driver

            # Create streaming lists
            # ts = time stamp; wls = wavelengths; ps = OPO power
            self.ts_average  = StreamingList() # (ts_initial + ts_final) /2
            self.ts_initial  = StreamingList()
            self.ts_final    = StreamingList()
            self.wls_average = StreamingList() # (wls_initial + wls_final) /2 for each average
            self.wls_initial = StreamingList()
            self.wls_final   = StreamingList()
            self.ps_average  = StreamingList() # (ps_initial + ps_final) /2
            self.ps_initial  = StreamingList()
            self.ps_final    = StreamingList()
            self.counts      = StreamingList()

            self.startTime = time.time()

            # Set OPO piezo to scan continuously
            cwave.scan_OPO_piezo(min_piezo, max_piezo, scan_rate)

            for n in range(num_points):
                t0 = time.time()
                #wl0 = wlm.get_wavelength()
                wl0 = 100
                p0 = cwave.get_status().pdOpoPower

                channel_num = int(data_channel.split("/"[1][3:])) # from "Dev1/PFI123" get 123 as an integer
                #data = daq.readCtr_multi_internalClk(sampling_rate, int(1/measure_rate),ctrChannelNums=[channel_num])
                data = [3.14]
                time.sleep(1/measure_rate)

                #wl1 = wlm.get_wavelength()
                t1 = time.time()
                wl1 = 101 + (t1-self.startTime)
                p1 = cwave.get_status().pdOpoPower

                # Calculate and store data
                self.ts_average.append(0.5*(t0+t1)-self.startTime)
                self.ts_initial.append(t0-self.startTime)
                self.ts_final.append(t1-self.startTime)
                self.wls_average.append(0.5*(wl0+wl1))
                self.wls_initial.append(wl0)
                self.wls_final.append(wl1)
                self.ps_average.append(0.5*(p0+p1))
                self.ps_initial.append(p0)
                self.ps_final.append(p1)
                self.counts.append(data[0])

                # Push data to dataserv
                cwavePLE_data.push(
                    {'params' :{ 'min_piezo' : min_piezo,
                                 'max_piezo' : max_piezo,
                                 'scan_rate' : scan_rate,
                                 'num_points': num_points,
                                 'measure_rate': measure_rate,
                                 'data_channel': data_channel,
                                 'ctr_channel' : ctr_channel,
                                 'sampling_rate': sampling_rate,
                                },              
                     'title': 'PLE using C-WAVE laser',
                     'xlabel': 'Wavelength (nm)',
                     'ylabel': 'Counts',
                     'datasets':{'Time of measurement (s)' : self.ts_average,
                                 'Wavelength during measurement (nm)' : self.wls_average,
                                 'Power during measurement (W)' : self.ps_average,
                                 'Counts during measurement (counts)' : self.counts
                                 
                         
                                }}
                )

            # stop OPO from scanning continuously, set to 50% output
            cwave.stop_OPO_piezo(50)
                

if __name__ == '__main__':
    exp = cwaveExperiment()
    exp.cwaveTrace(1,10,'cwaveTrace')