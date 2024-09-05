import time
import logging
from pathlib import Path
from itertools import count
import numpy as np

from nspyre import nspyre_init_logger
from nspyre import StreamingList, DataSource, experiment_widget_process_queue

from rosetta.drivers.ni.ni_motionControl import nidaqMotionControl
from rosetta.insmgr import MyInstrumentManager
from rpyc.utils.classic import obtain

_HERE = Path(__file__).parent
_logger = logging.getLogger(__name__)


class fsmScanExperiment:

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
        _logger.info('Created fsmExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed fsmExperiment instance.')

    def fsmScanMeasurement(self,    center_scan: bool,
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
        with MyInstrumentManager() as mgr, DataSource(dataset) as fsm_data:
            daq = mgr.ni_motionControl


            # Determine scope of scan
            if center_scan == True:
                initial_point = {'x': point1x - num_pixels_x/2 * pixel_resolution, 'y': point1y + num_pixels_y/2 * pixel_resolution}
                final_point   = {'x': point1x + num_pixels_x/2 * pixel_resolution, 'y': point1y - num_pixels_y/2 * pixel_resolution}

            elif center_scan == False:
                initial_point = {'x': point1x, 'y': point1y}
                final_point   = {'x': point2x, 'y': point2y}

            # Check/fix types
            num_pixels_x = int(num_pixels_x)
            num_pixels_y = int(num_pixels_y)
            avgs_per_pixel = int(avgs_per_pixel)


            rates    = np.zeros((num_pixels_y,num_pixels_x))
            x_min    = initial_point['x']
            x_max    = final_point['x']
            x_values = np.linspace(initial_point['x'],final_point['x'],num_pixels_x) # For saving in dataset.push
            y_values = np.linspace(initial_point['y'],final_point['y'],num_pixels_y)

            # Generate nice tick labels
            x_ticks = x_values
            y_ticks = y_values

            points_array = []

            for y_value, i in zip(y_values, range(len(y_values))):

                left_point = {'x': x_min, 'y': y_value}
                right_point = {'x': x_max, 'y': y_value}

                points = [(x_ticks[i],y_value) for i in range(len(x_ticks))]
                points_array.append(points)

                # rows going left to right
                if i % 2 == 0:
                    print(scan_rate)
                    print(avgs_per_pixel)
                    rates_in_row = obtain(daq.oneD_scan(left_point,right_point,num_pixels_x,scan_rate,avgs_per_pixel,data_channel))

                # rows going right to left
                else:
                    rates_in_row = obtain(daq.oneD_scan(right_point,left_point,num_pixels_x,scan_rate,avgs_per_pixel,data_channel))
                    rates_in_row = np.flip(rates_in_row)

                rates[i] = rates_in_row

                # save the current data to the data server
                fsm_data.push({'params'  :{ 'Dataset Name'          : dataset,
                                        'Top left corner (um)'      : initial_point,
                                        'Bottom right corner (um)'  : final_point,
                                        'Number of x pixels'        : num_pixels_x,
                                        'Number of y pixels'        : num_pixels_y,
                                        'Pixel scan rate (Hz)'      : scan_rate,
                                        'Time per pixel (s)'        : 1/scan_rate,
                                        'DAQ averages per pixel'    : avgs_per_pixel,
                                        'DAQ acquisition rate (Hz)' : scan_rate*avgs_per_pixel,
                                        'DAQ acquisition channel'   : data_channel},
                                        'Title'                     : '2D FSM Scan',
                                        'xlabel'                    : 'x (um)',
                                        'ylabel'                    : 'y (um)',
                                        'xticks'                    : x_ticks,
                                        'yticks'                    : y_ticks,
                            'datasets':{'points'                    : points_array,
                                        'x_ticks'                   : x_ticks,
                                        'y_ticks'                   : y_ticks,
                                        'rates'                     : rates}
                                 })
                
                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    return   

            # Save final position
            daq.set_position = final_point

    def fsmMoveMeasurement(self, x_coord:float, y_coord:float):
        with MyInstrumentManager() as mgr:
            daq = mgr.ni_motionControl

            point = {'x':x_coord,'y':y_coord}

            daq.move(point)

if __name__ == '__main__':
    exp = fsmScanExperiment()
    exp.fsmScanMeasurement(center_scan = False,
                       point1x     = -5,
                       point1y     = 5,
                       point2x     = 5,
                       point2y     = -5,
                       pixel_resolution = 1,
                       num_pixels_x = 20,
                       num_pixels_y = 20,
                       scan_rate = 50,
                       avgs_per_pixel = 20,
                       data_channel = 'Dev1/PFI1',
                       autosave = False,
                       autosave_interval = 60,
                       dataset = 'fsmData'
                       )