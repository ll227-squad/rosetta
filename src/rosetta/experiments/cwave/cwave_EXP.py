import time
import logging
import enum
from pathlib import Path
from itertools import count
import numpy as np

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

    def cwavePLE(self, dataset:str, min_piezo:float, max_piezo:float, scan_rate:float, num_points:int, 
                                    acq_rate:float, num_samples:int,
                                    data_channel:str):
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
            acq_rate (Hz): Frequency at which DAQ samples data_channel
            num_samples (int): Number of times to sample DAQ per point
            data_channel: e.g. Dev1/PFI1
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
                data = np.average(daq.readCtr_multi_internalClk(acq_rate,num_samples,ctrChannelNums=[channel_num]))

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
                                 'sampling_rate': sampling_rate,
                                },              
                     'title': 'PLE using C-WAVE laser',
                     'xlabel': 'Wavelength (nm)',
                     'ylabel': 'Counts',
                     'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                     'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                     'datasets':{'Time of measurement (s)' : self.ts_average,
                                 'Wavelength during measurement (nm)' : self.wls_average,
                                 'Power during measurement (W)' : self.ps_average,
                                 'Counts during measurement (counts)' : self.counts
                                 
                         
                                }}
                )

            # stop OPO from scanning continuously, set to 50% output
            cwave.stop_OPO_piezo(50)

    def cwavePLElockedExperiment(self, dataset: str,
                             wavelength_min,
                             iterations,
                             subscan_spacing,
                             num_subscans,
                             subscan_width,
                             num_points_per_subscan,
                             record_power,
                             acq_rate,
                             num_samples,
                             SNSPD_channel,
                             comments):

        with MyInstrumentManager() as mgr, DataSource(dataset) as cwavePLElocked_data:
            # Connect to C-Wave and DAQ
            cwave = mgr.cwave_driver
            cwave.connect('192.168.202.10')
            daq = mgr.ni_photonCounting
            if record_power==True:
                pm  = mgr.powerMeter_driver
                pm.set_correction_wavelength(wavelength_min) # send as nm
                calibration_wavelength = pm.get_correction_wavelength()
            else:
                calibration_wavelength = None

            snspd_ch = [int(SNSPD_channel[-1])]

            power_data = StreamingList()
            signal_data = StreamingList()

            #wavelengths = np.linspace(wavelength_min, wavelength_max, num_points)
            subscan_wavelengths = np.arange(wavelength_min,wavelength_min+num_subscans*subscan_spacing,subscan_spacing)

            # Open pump shutter
            #cwave.set_shutter(gtr.ShutterChannel.Pump, True)
            

            # Set wavelength close to starting point
            

            # Wait until wavelength dialing done


            #wait_for('Waiting for WLM Reading', lambda: (not math.isnan(cwave.get_status_all().measuredWavelength)))
            

            # Enable AbsoluteLambda
             # this is the equivalent of clcking the "AbsoluteLambda" button

            

            #WLM_WAVELENGTH = cwave.get_status().wlmSetpoint
            #print('Stabilizing to {:.7f}nm'.format(WLM_WAVELENGTH))

            # for loop
            for i in range(iterations):
                for j in range(len(subscan_wavelengths)):
                    subsection_wavelength = subscan_wavelengths[j].item()

                    # Dial the temperature of the OPO crystal
                    cwave.set_stabilize_wlm(False)
                    cwave.set_lambda(subsection_wavelength, False) # False means no SHG

                    # wait for device to finish dialing (poll for get_dial_done() == True)
                    wait_for('Waiting for device to dial wavelength', cwave.get_dial_done)
                    # let the device stabilize for a few seconds
                    wait(2)

                    current_wavelength = cwave.get_status().measuredWavelength
                    cwave.set_stabilize_wlm(True)
                    wavelengths = np.linspace(current_wavelength, current_wavelength+subscan_width, num_points_per_subscan)

                    signal_empty = np.empty(num_points_per_subscan)
                    signal_empty[:] = np.nan
                    signal_data.append(np.stack([wavelengths, signal_empty]))

                    power_empty = np.empty(num_points_per_subscan)
                    power_empty[:] = np.nan
                    power_data.append(np.stack([wavelengths, power_empty]))

                    for w, wavelength in enumerate(wavelengths):
                        wavelength = wavelength.item()
                        cwave.set_wlm_setpoint(wavelength)
                        print('Stabilizing to {:.7f}nm'.format(wavelength))
                        time.sleep(2)
                        signal = np.average(daq.readCtrs_multi_internalClk(acq_rate, num_samples, snspd_ch))
                        if record_power==True:
                            current_optical_power = pm.get_power() * 1e3 #mW
                        else:
                            current_optical_power = 1.0
                        signal_data[-1][1][w] = signal
                        signal_data.updated_item(-1)
                        power_data[-1][1][w] = current_optical_power #mW
                        power_data.updated_item(-1)
                        time.sleep(0.5)

                                            # save the current data to the data server.
                        cwavePLElocked_data.push({'params': {'wavelength_min_nm': wavelength_min,
                                                    'iterations': iterations,
                                                    'subscan_spacing_nm':subscan_spacing,
                                                    'num_subsections': num_subscans,
                                                    'subscan_width_nm':subscan_width,
                                                    'num_points_per_subscan': num_points_per_subscan,
                                                    'record_power' : record_power,
                                                    'power_meter_calibration_wavelength': calibration_wavelength,
                                                    'acq_rate' : acq_rate,
                                                    'num_samples' :num_samples,
                                                    'SNSPD_channel': SNSPD_channel,
                                                    'comments': comments},
                                        'title': 'Photoluminescence Excitation',
                                        'xlabel': 'Wavelength (nm)',
                                        'ylabel': 'Counts per {t:.3}s'.format(t=1/acq_rate),
                                        'credit': 'Chloe Washabaugh, washabaugh@uchicago.edu',
                                        'time'  : time.strftime("%D %T", time.gmtime(time.time())) + " UTC",
                                        'datasets': {'signal' : signal_data,
                                                     'power'  : power_data,}
                        })
                        if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                            # the GUI has asked us nicely to exit
                            return
                    time.sleep(0.5)


def wait_for(message: str, condition) -> None:
    '''Wait for a condition as lambda while giving console feedback'''
    char_list = ['|', '/', '-', '\\']
    char_index = 0
    last_len = 0
    while not condition():
        output_msg = '\r[{}] {}'.format(
            char_list[char_index],
            message
        )
        print(output_msg.ljust(last_len, ' '), end='')
        last_len = len(output_msg)
        char_index = (char_index + 1) % len(char_list)
        time.sleep(0.1)
    print(''.ljust(last_len, ' '), end='\r')
    print('[{}] {}'.format('X', message))

def wait(duration: float):
    '''Wait for certain time while giving console feedback'''
    start_time = time.perf_counter()
    wait_for('Waiting for {} seconds'.format(duration),
             lambda: time.perf_counter() - start_time >= duration
            )            
                

if __name__ == '__main__':
    exp = cwaveExperiment()
    #exp.cwaveTrace(1,10,'cwaveTrace')
    #exp.cwavePLElockedExperiment('cwavePLElocked',1050.5,1050.15,31,1,0.03,10,10,"/Dev1/PFI1","none")