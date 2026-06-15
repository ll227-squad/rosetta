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

import rosetta.experiments.eom.eom_EXP

class eomSRSWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('eomScan')
            },
            'laser_power': {
                'display_text': 'Laser Power (mW)',
                'widget': SpinBox(
                    value=0, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
            'laser_frequency': {
                'display_text': 'Laser Frequency (nm)',
                'widget': SpinBox(
                    value=1050.26, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
             'mw_power': {
                'display_text': 'MW Power (dBm)',
                'widget': SpinBox(
                    value=10, 
                    bounds=(-60, 16.5), 
                    dec=True),
            },
            'mw_start_frequency': {
                'display_text': 'Start Frequency (MHz)',
                'widget': SpinBox(
                    value=1e-3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(0, 40e3),
                    dec=True,
                ),
            },
            'mw_stop_frequency': {
                'display_text': 'Stop Frequency (MHz)',
                'widget': SpinBox(
                    value=6e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(0, 40e3),
                    dec=True,
                ),
            },
            'log' : {
                'display_text':'Log Scale for x-axis?',
                'widget': QtWidgets.QCheckBox()
            },
            'num_points': {
                'display_text': 'Number of Scan Points',
                'widget': SpinBox(
                    value=101, 
                    int=True, 
                    bounds=(1, None), 
                    dec=True),
            },
            'iterations': {
                'display_text': 'Number of Experiment Repeats',
                'widget': SpinBox(
                    value=1, 
                    int=True, 
                    bounds=(1, None), 
                    dec=True),
            },
            'readout_delay': {
                'display_text': 'Readout Delay (ms)',
                'widget': SpinBox(
                    value=1, 
                    suffix='ms',
                    bounds=(1e-6, 10e3), 
                    dec=True),
            },
            'acq_rate': {
                'display_text': 'DAQ Sampling Rate (Hz)',
                'widget': SpinBox(
                    value=1000, 
                    bounds=(1e-6, 10e3), 
                    dec=True),
            },
            'num_samples': {
                'display_text': 'DAQ Samples per Point',
                'widget': SpinBox(
                    value=50,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            'SNSPD_channel' : {
                'display_text': 'DAQ PFI Channel For SNSPD',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI1')
            },
            'comments' : {
                'display_text' : 'Comments',
                'widget' : QtWidgets.QLineEdit('SRS396;')
            },
        }
        super().__init__(params_config, 
                        module =    rosetta.experiments.eom.eom_EXP,
                        cls =      'eomExperiment',
                        fun_name = 'eomSRSScan',
                        title=     'EOM Sweep with SRS and SNSPD')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

class eomSRStransientWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('eomScan')
            },
            'laser_power': {
                'display_text': 'Laser Power (mW)',
                'widget': SpinBox(
                    value=0, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
            'laser_frequency': {
                'display_text': 'Laser Frequency (nm)',
                'widget': SpinBox(
                    value=1050.28, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
            't_aom_delay': {
                'display_text': 'AOM Delay (us)',
                'widget': SpinBox(
                    value=1.073, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_laser_on': {
                'display_text': 'Laser On Time (us)',
                'widget': SpinBox(
                    value=1000, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_laser_off': {
                'display_text': 'Laser Off Time (us)',
                'widget': SpinBox(
                    value=8000, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
             'mw_power': {
                'display_text': 'MW Power (dBm)',
                'widget': SpinBox(
                    value=14, 
                    bounds=(-60, 16.5), 
                    dec=True),
            },
            'mw_start_frequency': {
                'display_text': 'Start Frequency (MHz)',
                'widget': SpinBox(
                    value=1e-3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(0, 40e3),
                    dec=True,
                ),
            },
            'mw_stop_frequency': {
                'display_text': 'Stop Frequency (MHz)',
                'widget': SpinBox(
                    value=6e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(0, 40e3),
                    dec=True,
                ),
            },
            'num_points': {
                'display_text': 'Number of Scan Points',
                'widget': SpinBox(
                    value=101, 
                    int=True, 
                    bounds=(1, None), 
                    dec=True),
            },
            'iterations': {
                'display_text': 'Number of Experiment Repeats',
                'widget': SpinBox(
                    value=1, 
                    int=True, 
                    bounds=(1, None), 
                    dec=True),
            },
            'num_samples': {
                'display_text': 'DAQ Samples per Point',
                'widget': SpinBox(
                    value=50,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            'daq_cts_channel' : {
                'display_text': 'DAQ PFI Channel For SNSPD',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI1')
            },
            'daq_trig_channel' : {
                'display_text': 'DAQ PFI Channel For Trigger',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI2')
            },
            'daq_clk_channel' : {
                'display_text': 'DAQ PFI Channel For Clock',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI3')
            },
            'ps_EN_channel' : {
                'display_text': 'Pulse Streamer to rf switch EN',
                'widget': SpinBox(
                    value=0, 
                    int=True, 
                    bounds=(0, 8), 
                    dec=True),
            },
            'ps_CTRL_channel' : {
                'display_text': 'Pulse Streamer to rf switch CTRL',
                'widget': SpinBox(
                    value=1, 
                    int=True, 
                    bounds=(0, 8), 
                    dec=True),
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
            'ps_aomAnalog_channel' : {
                'display_text': 'Pulse Streamer to AOM Analog',
                'widget': SpinBox(
                    value=1, 
                    int=True, 
                    bounds=(0, 8), 
                    dec=True),
            },
            'comments' : {
                'display_text' : 'Comments',
                'widget' : QtWidgets.QLineEdit('SRS396;')
            },
        }
        super().__init__(params_config, 
                        module =    rosetta.experiments.eom.eom_EXP,
                        cls =      'eomExperiment',
                        fun_name = 'eomSRStransientScan',
                        title=     'EOM Sweep with SRS and SNSPD and Pulsed Laser')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

class eomE8257DWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('eomScan')
            },
            'laser_power': {
                'display_text': 'Laser Power (mW)',
                'widget': SpinBox(
                    value=0, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
            'laser_frequency': {
                'display_text': 'Laser Frequency (nm)',
                'widget': SpinBox(
                    value=1050.26, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
             'mw_power': {
                'display_text': 'MW Power (dBm)',
                'widget': SpinBox(
                    value=10, 
                    bounds=(-60, 16.5), 
                    dec=True),
            },
            'mw_start_frequency': {
                'display_text': 'Start Frequency (MHz)',
                'widget': SpinBox(
                    value=1e-3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(1e-9, 40e3),
                    dec=True,
                ),
            },
            'mw_stop_frequency': {
                'display_text': 'Stop Frequency (MHz)',
                'widget': SpinBox(
                    value=6e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(1e-9, 40e3),
                    dec=True,
                ),
            },
            'log' : {
                'display_text':'Log Scale for x-axis?',
                'widget': QtWidgets.QCheckBox()
            },
            'num_points': {
                'display_text': 'Number of Scan Points',
                'widget': SpinBox(
                    value=101, 
                    int=True, 
                    bounds=(1, None), 
                    dec=True),
            },
            'iterations': {
                'display_text': 'Number of Experiment Repeats',
                'widget': SpinBox(
                    value=1, 
                    int=True, 
                    bounds=(1, None), 
                    dec=True),
            },
            'readout_delay': {
                'display_text': 'Readout Delay (ms)',
                'widget': SpinBox(
                    value=1, 
                    suffix='ms',
                    bounds=(1e-6, 10e3), 
                    dec=True),
            },
            'acq_rate': {
                'display_text': 'DAQ Sampling Rate (Hz)',
                'widget': SpinBox(
                    value=1000, 
                    bounds=(1e-6, 10e3), 
                    dec=True),
            },
            'num_samples': {
                'display_text': 'DAQ Samples per Point',
                'widget': SpinBox(
                    value=1000,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            'SNSPD_channel' : {
                'display_text': 'DAQ PFI Channel For SNSPD',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI1')
            },
            'comments' : {
                'display_text' : 'Comments',
                'widget' : QtWidgets.QLineEdit('E8257D;')
            },
        }
        super().__init__(params_config, 
                        module =    rosetta.experiments.eom.eom_EXP,
                        cls =      'eomExperiment',
                        fun_name = 'eomE8257DScan',
                        title=     'EOM Sweep with Agilent E8257D and SNSPD')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

class eomE8257DwithMWcyclingWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('eomScan')
            },
            'laser_power': {
                'display_text': 'Laser Power (mW)',
                'widget': SpinBox(
                    value=0, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
            'laser_frequency': {
                'display_text': 'Laser Frequency (nm)',
                'widget': SpinBox(
                    value=1050.26, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
             'cycle_mw_power': {
                'display_text': 'Cycling MW Power (dBm)',
                'widget': SpinBox(
                    value=0, 
                    bounds=(-60, 4), 
                    dec=True),
            },
            'cycle_mw_frequency': {
                'display_text': 'Cycling MW Frequency (MHz)',
                'widget': SpinBox(
                    value=9.5e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(1e-9, 40e3),
                    dec=True,
                ),
            },
            'cycle_mw_off_on' : {
                'display_text': 'Cycling MW on (1) or off (0)',
                'widget': SpinBox(
                    value=0, 
                    int=True, 
                    bounds=(0, 1), 
                    dec=True),
            },
             'mw_power': {
                'display_text': 'EOM MW Power (dBm)',
                'widget': SpinBox(
                    value=10, 
                    bounds=(-60, 16.5), 
                    dec=True),
            },
            'mw_start_frequency': {
                'display_text': 'Start Frequency (MHz)',
                'widget': SpinBox(
                    value=1e-3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(1e-9, 40e3),
                    dec=True,
                ),
            },
            'mw_stop_frequency': {
                'display_text': 'Stop Frequency (MHz)',
                'widget': SpinBox(
                    value=6e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(1e-9, 40e3),
                    dec=True,
                ),
            },
            'num_points': {
                'display_text': 'Number of Scan Points',
                'widget': SpinBox(
                    value=101, 
                    int=True, 
                    bounds=(1, None), 
                    dec=True),
            },
            'iterations': {
                'display_text': 'Number of Experiment Repeats',
                'widget': SpinBox(
                    value=1, 
                    int=True, 
                    bounds=(1, None), 
                    dec=True),
            },
            'readout_delay': {
                'display_text': 'Readout Delay (ms)',
                'widget': SpinBox(
                    value=1, 
                    suffix='ms',
                    bounds=(1e-6, 10e3), 
                    dec=True),
            },
            'acq_rate': {
                'display_text': 'DAQ Sampling Rate (Hz)',
                'widget': SpinBox(
                    value=1000, 
                    bounds=(1e-6, 10e3), 
                    dec=True),
            },
            'num_samples': {
                'display_text': 'DAQ Samples per Point',
                'widget': SpinBox(
                    value=1000,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            'SNSPD_channel' : {
                'display_text': 'DAQ PFI Channel For SNSPD',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI1')
            },
            'ps_channel_EN' : {
                'display_text': 'Pulse Streamer to rf switch EN',
                'widget': SpinBox(
                    value=0, 
                    int=True, 
                    bounds=(0, 8), 
                    dec=True),
            },
            'ps_channel_CTRL' : {
                'display_text': 'Pulse Streamer to rf switch CTRL',
                'widget': SpinBox(
                    value=1, 
                    int=True, 
                    bounds=(0, 8), 
                    dec=True),
            },
            'ps_channel_DAQ' : {
                'display_text': 'Pulse Streamer to DAQ PFI',
                'widget': SpinBox(
                    value=2, 
                    int=True, 
                    bounds=(0, 8), 
                    dec=True),
            },
            'ps_channel_AOM' : {
                'display_text': 'Pulse Streamer to AOM',
                'widget': SpinBox(
                    value=4, 
                    int=True, 
                    bounds=(0, 8), 
                    dec=True),
            },
            'comments' : {
                'display_text' : 'Comments',
                'widget' : QtWidgets.QLineEdit('E8257D;')
            },
        }
        super().__init__(params_config, 
                        module =    rosetta.experiments.eom.eom_EXP,
                        cls =      'eomExperiment',
                        fun_name = 'eomE8257DwithMWcyclingScan',
                        title=     'EOM Sweep with Agilent E8257D, cycling MWs, and SNSPD')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

class FlexLinePlotWidgetWithEOMScanDefaults(FlexLinePlotWidget):
    """Add some default settings to the FlexSinkLinePlotWidget."""
    def __init__(self):
        super().__init__()
        # create some default signal plots
        self.add_plot('signal',        series='signal',   scan_i='',     scan_j='',  processing='Average')

        # retrieve legend object
        legend = self.line_plot.plot_widget.addLegend()
        # set the legend location
        legend.setOffset((-10, -50))

        self.datasource_lineedit.setText('eomScan')