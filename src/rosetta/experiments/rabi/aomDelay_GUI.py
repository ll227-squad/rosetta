from functools import partial
from importlib import reload
import numpy as np

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox
from nspyre import ParamsWidget
from nspyre import ProcessRunner
from nspyre import DataSink
from nspyre import ExperimentWidget
from nspyre import FlexLinePlotWidget

import rosetta.experiments.rabi.aomDelay_EXP

class aomDelayWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('aomDelay')
            },
            'laser_power': {
                'display_text': 'Laser Power (mW)',
                'widget': SpinBox(
                    value=0, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
            'start_aom': {
                'display_text': 'Open AOM at (us)',
                'widget': SpinBox(
                    value=20, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            'photon_read_window': {
                'display_text': 'Photon Read Window (us)',
                'widget': SpinBox(
                    value=10, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            'aom_on_window': {
                'display_text': 'AOM On Window (us)',
                'widget': SpinBox(
                    value=20, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            'num_points': {
                'display_text': 'Number of Points (delays)',
                'widget': SpinBox(
                    value=101,
                    int=True, 
                    bounds=(2, 10e3), 
                    dec=True),
            },
            'avgs_per_point': {
                'display_text': 'Averages per Point',
                'widget': SpinBox(
                    value=1,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            'daq_cts_channel' : {
                'display_text': 'DAQ PFI Channel For SNSPD',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI1')
            },
            'ps_trig_channel' : {
                'display_text': 'Pulse Streamer to DAQ Trig',
                'widget': SpinBox(
                    value=2, 
                    int=True, 
                    bounds=(0, 8), 
                    dec=True),
            },
            'ps_clk_channel' : {
                'display_text': 'Pulse Streamer to DQ Clk',
                'widget': SpinBox(
                    value=3, 
                    int=True, 
                    bounds=(0, 8), 
                    dec=True),
            },
            'ps_aom_channel' : {
                'display_text': 'Pulse Streamer to AOM',
                'widget': SpinBox(
                    value=4, 
                    int=True, 
                    bounds=(0, 8), 
                    dec=True),
            },
            'comments' : {
                'display_text' : 'Comments',
                'widget' : QtWidgets.QLineEdit()
            },}
        super().__init__(params_config, 
                module =    rosetta.experiments.rabi.aomDelay_EXP,
                cls =      'aomDelayExperiment',
                fun_name = 'aomDelayExperiment',
                title=     'Measure AOM Delay')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""


class FlexLinePlotWidgetWithAOMDelayDefaults(FlexLinePlotWidget):
    """Add some default settings to the FlexSinkLinePlotWidget."""
    def __init__(self):
        super().__init__()
        # create some default signal plots
        self.add_plot('signal',        series='signal',   scan_i='',     scan_j='',  processing='Average')
        self.add_plot('should start to increase counts',        series='aom_on_time',   scan_i='',     scan_j='', processing='Average')
        self.add_plot('should start to decrease counts',        series='aom_off_time',   scan_i='',     scan_j='', processing='Average')

        # retrieve legend object
        legend = self.line_plot.plot_widget.addLegend()
        # set the legend location
        legend.setOffset((-10, -50))

        self.datasource_lineedit.setText('aomDelay')