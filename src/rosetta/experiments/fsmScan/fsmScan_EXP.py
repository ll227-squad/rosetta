import time
import logging
from pathlib import Path
from itertools import count
import numpy as np

from nspyre import nspyre_init_logger
from nspyre import StreamingList, DataSource, experiment_widget_process_queue

from rosetta.drivers.ni.ni_motionControl import nidaqMotionControl
from rosetta.insmgr import MyInstrumentManager

_HERE = Path(__file__).parent
_logger = logging.getLogger(__name__)


class FSMExperiment:
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
        _logger.info('Created FSMExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed FSMExperiment instance.')

    def FSM2DMeasurement(self,  center_scan: bool,
                                point1x: float,
                                point1y: float,
                                point2x: float,
                                point2y: float,
                                pixel_resolution: float,
                                num_pixels_x: int, 
                                num_pixels_y: int, 
                                scan_rate: float, 
                                avgs_per_pixel: int, 
                                data_channel: str, 
                                autosave: bool, 
                                autosave_interval: int, 
                                dataset:str, **kwargs):
        '''
        Perform a 2D scan of an area specified by top left corner initial_point and bottom right corner final_point. Image will be formed with
        num_pixels_x and num_pixels_y pixels in each respective direction.

        The 2D scan is rastered; that is, the scan will snake from the top left corner to the top right corner, hop down (-y) one pixel and return
        scanning to the right. This pattern repeats until the end of the raster scan. The data acquired on data_channel will be pushed to the data server
        every line scan.

        A 2D scan is formed by calling oneD_scan(num_pixels = num_pixels_x) num_pixels_y number of times. Data is collected on each pixel for 
        1/scan_rate seconds. Data is collected on DAQ channel data_channel (currently configured to only sample digital inputs/TTL pulses) avgs_per_pixel
        number of times per pixel. The raw counts are then averaged over each pixel and normalized to time.

        This method returns a 2D numpy array that is num_pixels_x by num_pixels_y in size. Each element is the cps (Hz) recorded by the DAQ
        during the time the FSM dwelled at each pixel.

        This method is essentially the same as twoD_scan in ni_motionControl.py. However, in order to push data to the data server for each line scan,
        we recreate the twoD_scan method here.

        Arguments:
                *inital_point: dictionary giving top left corner for the 2D scan (in um),  e.g. {'x': -10, 'y': 10}
                *final_point: dictionary giving bottom right corner for the 2D scan (in um), e.g. {'x': 10, 'y':-10}
                *num_pixels_x: number of dwell points for the 2D scan in the x-direction
                *num_pixels_y: number of dwell points for the 2D scan in the y-direction
                *scan_rate: rate/dwell time of collection for the 2D scan on each pixel
                *avgs_per_pixel: for each pixel, read the DAQ this many times and average the result
                *data_channel: physical DAQ channel that collects data (default: PFI channel for collecting digital pulses)
        '''
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as FSM_data:
            daq = mgr.ni_motionControl

            # Determine scope of scan
            if center_scan == True:
                initial_point = {'x': point1x - num_pixels_x/2 * pixel_resolution, 'y': point1y + num_pixels_y/2 * pixel_resolution}
                final_point   = {'x': point1x + num_pixels_x/2 * pixel_resolution, 'y': point1y - num_pixels_y/2 * pixel_resolution}

            elif center_scan == False:
                initial_point = {'x': point1x, 'y': point1y}
                final_point   = {'x': point2x, 'y': point2y}


            rates    = np.zeros((num_pixels_y,num_pixels_x))
            x_min    = initial_point['x']
            x_max    = final_point['x']
            x_values = np.linspace(initial_point['x'],final_point['x'],num_pixels_x) # For saving in dataset.push
            y_values = np.linspace(initial_point['y'],final_point['y'],num_pixels_y)

            # Generate nice tick labels
            x_ticks = np.round(x_values,2)
            y_ticks = np.round(y_values,2)

            points_array = []

            for y_value, i in zip(y_values, range(len(y_values))):

                left_point = {'x': x_min, 'y': y_value}
                right_point = {'x': x_max, 'y': y_value}

                points = [(x_ticks[i],y_value) for i in range(len(x_ticks))]
                points_array.append(points)

                # rows going left to right
                if i % 2 == 0:
                    rates_in_row = daq.oneD_scan(left_point,right_point,num_pixels_x,scan_rate,avgs_per_pixel,data_channel)

                # rows going right to left
                else:
                    rates_in_row = daq.oneD_scan(right_point,left_point,num_pixels_x,scan_rate,avgs_per_pixel,data_channel)
                    rates_in_row = np.flip(rates_in_row)

                rates[i] = rates_in_row

                        # save the current data to the data server
                FSM_data.push({'params'  :{ 'Dataset Name'          : dataset,
                                        'Top left corner (um)'      : initial_point,
                                        'Bottom right corner (um)'  : final_point,
                                        'Number of x pixels'        : num_pixels_x,
                                        'Number of y pixels'        : num_pixels_y,
                                        'Pixel scan rate (Hz)'      : scan_rate,
                                        'DAQ averages per pixel'    : avgs_per_pixel,
                                        'DAQ acquisition rate (Hz)' : scan_rate*avgs_per_pixel,
                                        'DAQ acquisition channel'   : data_channel},
                                        'Title'                     : '2D FSM Scan',
                                        'xlabel'                    : 'x (um)',
                                        'ylabel'                    : 'y (um)',
                                        'xticks'                    : x_ticks,
                                        'yticks'                    : y_ticks,
                            'datasets':{'points'                    : points_array,
                                        'rates'                     : rates}
                                 })
                
                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    return   

            # Save final position
            daq.set_position = final_point

 


if __name__ == '__main__':
    exp = FSMExperiment()
    exp.FSM2DMeasurement(center_scan = False,
                       point1x = -1,
                       point1y = 1,
                       point2x = 1,
                       point2y = -1,
                       pixel_resolution = 1,
                       num_pixels_x = 10,
                       num_pixels_y = 10,
                       scan_rate = 100,
                       avgs_per_pixel = 20,
                       data_channel = 'Dev1/PFI1',
                       autosave = False,
                       autosave_interval = 60,
                       dataset = 'FSMMeasurement')