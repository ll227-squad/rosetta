"""
GUI for a Fsm Scan Application

Copyright (c) May 2023, Chris Egerstrom

Edited June 2024, Chloe Washabaugh
All rights reserved.

This work is licensed under the terms of the 3-Clause BSD license.
For a copy, see <https://opensource.org/licenses/BSD-3-Clause>.
"""

from functools import partial
from importlib import reload

from pyqtgraph.Qt import QtWidgets, QtCore
from pyqtgraph import SpinBox
from multiprocessing import Queue
from nspyre import ParamsWidget
from nspyre import ProcessRunner
from nspyre import DataSink
from nspyre.gui.widgets.heatmap import HeatMapWidget
from nspyre import ExperimentWidget

import rosetta.experiments.fsmScan.fsmScan_EXP


class fsmScanWidget(ExperimentWidget):
    def __init__(self):

        params_config = {
          
            'point1x' : {
                'display_text': 'Top left point (or center) x (m)',
                'widget': SpinBox(
                    value = -1e-6,
                    suffix = 'm',
                    siPrefix = True,
                    bounds = (-50e-6,50e6),
                    dec = True
                ),
            },

            'point1y' : {
                'display_text': 'Top left point (or center) y (m)',
                'widget': SpinBox(
                    value = 1e-6,
                    suffix = 'm',
                    siPrefix = True,
                    bounds = (-50e-6,50e6),
                    dec = True
                ),
            },

            'point2x' : {
                'display_text': 'Bottom right x (m)',
                'widget': SpinBox(
                    value = 1e-6,
                    suffix = 'm',
                    siPrefix = True,
                    bounds = (-50e-6,50e6),
                    dec = True
                ),
            },

            'point2y' : {
                'display_text': 'Bottom right y (m)',
                'widget': SpinBox(
                    value = -1e-6,
                    suffix = 'm',
                    siPrefix = True,
                    bounds = (-50e-6,50e6),
                    dec = True
                ),
            },

            'center_scan' : {
                'display_text': 'Center scan on a point?',
                'widget': QtWidgets.QCheckBox(),
            },
            'pixel_resolution': {
                'display_text': 'Pixel spacing for center scan (m)',
                'widget': SpinBox(
                    value = 1e-6,
                    suffix = 'm',
                    siPrefix = True,
                    bounds = (0,10e6),
                    dec = True
                ),
            },
             'num_pixels_x': {
                'display_text': '# of pixels in x-direction',
                'widget': SpinBox(
                    value = 20,
                    bounds = (1,40),
                    dec = False
                ),
            },
            'num_pixels_y': {
                'display_text': '# of pixels in y-direction',
                'widget': SpinBox(
                    value = 20,
                    bounds = (1,40),
                    dec = False
                ),
            },
            'scan_rate': {
                'display_text': 'Pixel scan rate (Hz)',
                'widget': SpinBox(
                    value = 10,
                    suffix = 'Hz',
                    siPrefix = True,
                    bounds = (1e-3,10e3),
                    dec = False
                ),
            },
            'avgs_per_pixel' : {
                'display_text': '# of DAQ samples per pixel',
                'widget':SpinBox(
                    value=20,
                    bounds=(1, 1e3),
                    dec=True,
                )
            },
            'data_channel' : {
                'display_text': 'DAQ counting channel',
                'widget': QtWidgets.QLineEdit('Dev1/PFI1')
            },            
            
            'autosave' : {
                'display_text': 'Autosave?',
                'widget': QtWidgets.QCheckBox()
            },

            'autosave_interval' : {
                'display_text': 'Autosave interval (s)',
                'widget':SpinBox(
                    value=60,
                    suffix='s',
                    siPrefix=True,
                    bounds=(-1, 1e6),
                    dec=True,
                )
            },
            'dataset' : {
                'display_text': 'Dataset Name',
                'widget': QtWidgets.QLineEdit('fsmScan')
            }
        }

        super().__init__(params_config, 
                        module =    rosetta.experiments.fsmScan.fsmScan_EXP,
                        cls =      'fsmScanExperiment',
                        fun_name = 'fsmScanMeasurement',
                        title=     '2D FSM Scan')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

class fsmMoveWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'x_coord' : {
                'display_text': 'Point x-coord (m)',
                'widget': SpinBox(
                    value = -1e-6,
                    suffix = 'm',
                    siPrefix = True,
                    bounds = (-50e-6,50e6),
                    dec = True
                ),
            },

            'y_coord' : {
                'display_text': 'Point y-coord (m)',
                'widget': SpinBox(
                    value = 1e-6,
                    suffix = 'm',
                    siPrefix = True,
                    bounds = (-50e-6,50e6),
                    dec = True
                ),
            },
        }

        super().__init__(params_config, 
                        module =    rosetta.experiments.fsmScan.fsmScan_EXP,
                        cls =      'fsmScanExperiment',
                        fun_name = 'fsmMoveMeasurement',
                        title=     'Move FSM')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

        #zeroButton = QtWidgets.QPushButton('Zero')
        #zeroButton.clicked.connect()

class fsmScanPlotWidget(HeatMapWidget):
    def __init__(self):
        title = 'FSM Scan'
        super().__init__(title=title, btm_label='X', lft_label='Y')


    def setup(self):
        self.sink = DataSink('fsmScan')
        self.sink.__enter__()


    def teardown(self):
        self.sink.__exit__()


    def update(self):
        self.sink.pop() #wait for some data to be saved to sink
        self.set_data(self.sink.datasets['x_ticks'], self.sink.datasets['y_ticks'], self.sink.datasets['rates'])