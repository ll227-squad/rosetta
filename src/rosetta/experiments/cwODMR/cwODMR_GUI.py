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

import rosetta.experiments.cwODMR.cwODMR_EXP

class mwPowerWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'rate' : {
                'display_text': 'Sampling Rate (Hz)',
                'widget':SpinBox(
                    value=1,
                    suffix='Hz',
                    siPrefix=True,
                    bounds=(1e-3, 1e2),
                    dec=True,
                )
            },
            'num_points' : {
                'display_text': 'Number of Points',
                'widget':SpinBox(
                    value=-1,
                    siPrefix=True,
                    bounds=(-1, 1e6),
                    dec=True,
                )
            },
            'AI_channel' : {
                'display_text': 'DAQ AI Channel',
                'widget': QtWidgets.QLineEdit('Dev1/AI0')
            },
            'dataset' : {
                'display_text': 'Dataset Name',
                'widget': QtWidgets.QLineEdit('mwpowervstime')
            }
        }

        super().__init__(params_config, 
                        module =    rosetta.experiments.cwODMR.cwODMR_EXP,
                        cls =      'mwPowerExperiment',
                        fun_name = 'mwPowerTrace',
                        title=     'MW Power Into Cryostat Trace')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

def process_mwPower_data(sink: DataSink):
    processed_dataset = []
    for s,_ in enumerate(sink.datasets['times']):
        ts = sink.datasets['times']
        ps = sink.datasets['powers']
        processed_dataset.append(np.stack([ts, ps]))
    sink.datasets['mwpowervstime_processed'] = processed_dataset

class FlexLinePlotWidgetWithPVTDefaults(FlexLinePlotWidget):
    """Add some default settings to the FlexSinkLinePlotWidget."""
    def __init__(self):
        super().__init__(data_processing_func = process_mwPower_data)
        # create some default signal plots
        self.add_plot(name = 'mwpowervstime',
                      series='mwpowervstime_processed',
                      scan_i='',
                      scan_j='',
                      processing='Average')

        # retrieve legend object
        legend = self.line_plot.plot_widget.addLegend()
        # set the legend location
        legend.setOffset((-10, -50))

        self.datasource_lineedit.setText('mwpowervstime')

class cwODMRfemtoWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('cwODMRfemto')
            },

            'start_freq': {
                'display_text': 'Start Frequency (MHz)',
                'widget': SpinBox(
                    value=1e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
                    dec=True,
                ),
            },
            'stop_freq': {
                'display_text': 'Stop Frequency (MHz)',
                'widget': SpinBox(
                    value=2e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
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
            'dwell_time': {
                'display_text': 'Dwell Time (ms)',
                'widget': SpinBox(
                    value=1, 
                    bounds=(1e-6, 10e3), 
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
             'mw_power': {
                'display_text': 'MW Power (dBm)',
                'widget': SpinBox(
                    value=-20, 
                    bounds=(-60, 4), 
                    dec=True),
            },
            'femto_channel' : {
                'display_text': 'DAQ AI Channel For Femto',
                'widget': QtWidgets.QLineEdit('Dev1/AI4')
            },
            'schottky_channel' : {
                'display_text': 'DAQ AI Channel For Schottky Diode',
                'widget': QtWidgets.QLineEdit('Dev1/AI0')
            },
        }
        super().__init__(params_config, 
                        module =    rosetta.experiments.cwODMR.cwODMR_EXP,
                        cls =      'cwODMRExperiment',
                        fun_name = 'cwODMRfemtoExperiment',
                        title=     'cwODMR with femto counts')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

class cwODMRsnspdWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('cwODMRsnspd')
            },

            'start_freq': {
                'display_text': 'Start Frequency (MHz)',
                'widget': SpinBox(
                    value=1e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
                    dec=True,
                ),
            },
            'stop_freq': {
                'display_text': 'Stop Frequency (MHz)',
                'widget': SpinBox(
                    value=2e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
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
            'laser_power': {
                'display_text': 'Laser Power (mW)',
                'widget': SpinBox(
                    value=0, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
            'laser_wavelength' : {
                'display_text': 'Laser Wavelength (nm)',
                'widget': SpinBox(
                    value=1050.28, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
             'mw_power': {
                'display_text': 'MW Power (dBm)',
                'widget': SpinBox(
                    value=-40, 
                    bounds=(-60, 4), 
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
                'display_text': 'DAQ Samples per Point\nacq_rate/num_samp >= sweep_rate*2',
                'widget': SpinBox(
                    value=50,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            'record_power' : {
                'display_text':'Record Power?',
                'widget': QtWidgets.QCheckBox()
            },
            'SNSPD_channel' : {
                'display_text': 'DAQ PFI Channel For SNSPD',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI1')
            },
            'PS_channel' : {
                'display_text': 'DAQ PFI Channel For PS Triggering',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI2')
            },
            'schottky_channel' : {
                'display_text': 'DAQ AI Channel For Schottky Diode',
                'widget': QtWidgets.QLineEdit('Dev1/AI0')
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
                'widget' : QtWidgets.QLineEdit('SRS396; ')
            },
        }
        super().__init__(params_config, 
                        module =    rosetta.experiments.cwODMR.cwODMR_EXP,
                        cls =      'cwODMRExperiment',
                        fun_name = 'cwODMRsnspdExperiment',
                        title=     'cwODMR with SNSPD counts')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

class cwODMRsnspdE8257DWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('cwODMRsnspd')
            },

            'start_freq': {
                'display_text': 'Start Frequency (MHz)',
                'widget': SpinBox(
                    value=9e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
                    dec=True,
                ),
            },
            'stop_freq': {
                'display_text': 'Stop Frequency (MHz)',
                'widget': SpinBox(
                    value=10e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
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
            'laser_power': {
                'display_text': 'Laser Power (Vaom)',
                'widget': SpinBox(
                    value=1, 
                    bounds=(0, 1), 
                    dec=True),
            },
            'laser_wavelength' : {
                'display_text': 'Laser Wavelength (nm)',
                'widget': SpinBox(
                    value=1050.28, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
             'mw_power': {
                'display_text': 'MW Power (dBm)',
                'widget': SpinBox(
                    value=-20, 
                    bounds=(-60, 2), 
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
                'display_text': 'DAQ Samples per Point\nacq_rate/num_samp >= sweep_rate*2',
                'widget': SpinBox(
                    value=50,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            'record_power' : {
                'display_text':'Record Power?',
                'widget': QtWidgets.QCheckBox()
            },
            'SNSPD_channel' : {
                'display_text': 'DAQ PFI Channel For SNSPD',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI1')
            },
            'PS_channel' : {
                'display_text': 'DAQ PFI Channel For PS Triggering',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI2')
            },
            'schottky_channel' : {
                'display_text': 'DAQ AI Channel For Schottky Diode',
                'widget': QtWidgets.QLineEdit('Dev1/AI0')
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
                'widget' : QtWidgets.QLineEdit('E8257D;')
            },
        }
        super().__init__(params_config, 
                        module =    rosetta.experiments.cwODMR.cwODMR_EXP,
                        cls =      'cwODMRExperiment',
                        fun_name = 'cwODMRsnspdE8257DExperiment',
                        title=     'cwODMR with SNSPD counts and E8257 sig gen')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

class cwODMRsnspdE8257DdutycycleWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('cwODMRsnspd')
            },

            'start_freq': {
                'display_text': 'Start Frequency (MHz)',
                'widget': SpinBox(
                    value=9e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
                    dec=True,
                ),
            },
            'stop_freq': {
                'display_text': 'Stop Frequency (MHz)',
                'widget': SpinBox(
                    value=10e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
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
            'laser_power': {
                'display_text': 'Laser Power (mW)',
                'widget': SpinBox(
                    value=0, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
            'laser_wavelength' : {
                'display_text': 'Laser Wavelength (nm)',
                'widget': SpinBox(
                    value=1050.28, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
             'mw_power': {
                'display_text': 'MW Power (dBm)',
                'widget': SpinBox(
                    value=-20, 
                    bounds=(-60, 2), 
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
            'duty_cycle': {
                'display_text': 'Duty Cycle (ratio)',
                'widget': SpinBox(
                    value = 0.5,
                    bounds = (0.05,0.5),
                    dec = True),
            },
            'acq_rate': {
                'display_text': 'DAQ Sampling Rate (Hz)',
                'widget': SpinBox(
                    value=1000, 
                    bounds=(1e-6, 10e3), 
                    dec=True),
            },
            'num_samples': {
                'display_text': 'DAQ Samples per Point\nacq_rate/num_samp >= sweep_rate*2',
                'widget': SpinBox(
                    value=50,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            'record_power' : {
                'display_text':'Record Power?',
                'widget': QtWidgets.QCheckBox()
            },
            'SNSPD_channel' : {
                'display_text': 'DAQ PFI Channel For SNSPD',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI1')
            },
            'PS_channel' : {
                'display_text': 'DAQ PFI Channel For PS Triggering',
                'widget': QtWidgets.QLineEdit('/Dev1/PFI2')
            },
            'schottky_channel' : {
                'display_text': 'DAQ AI Channel For Schottky Diode',
                'widget': QtWidgets.QLineEdit('Dev1/AI0')
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
                'widget' : QtWidgets.QLineEdit('E8257D;')
            },
        }
        super().__init__(params_config, 
                        module =    rosetta.experiments.cwODMR.cwODMR_EXP,
                        cls =      'cwODMRExperiment',
                        fun_name = 'cwODMRsnspdE8257DdutycycleExperiment',
                        title=     'cwODMR with SNSPD counts and E8257 sig gen and control over duty cycle')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

class cwODMRsnspdE8257DfastswitchingWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('cwODMRsnspd')
            },

            'start_freq': {
                'display_text': 'Start Frequency (MHz)',
                'widget': SpinBox(
                    value=9.4e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
                    dec=True,
                ),
            },
            'stop_freq': {
                'display_text': 'Stop Frequency (MHz)',
                'widget': SpinBox(
                    value=9.7e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
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
            'laser_power': {
                'display_text': 'Laser Power (Vaom)',
                'widget': SpinBox(
                    value=1, 
                    bounds=(0, 1), 
                    dec=True),
            },
            'laser_wavelength' : {
                'display_text': 'Laser Wavelength (nm)',
                'widget': SpinBox(
                    value=1050.261, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
             'mw_power': {
                'display_text': 'MW Power (dBm)',
                'widget': SpinBox(
                    value=-20, 
                    bounds=(-60, 2), 
                    dec=True),
            },
            'readout_delay': {
                'display_text': 'Readout Delay (ms)',
                'widget': SpinBox(
                    value=11, 
                    suffix='ms',
                    bounds=(1e-6, 10e3), 
                    dec=True),
            },
            'dwell_rate': {
                'display_text': 'MW Switching Rate (Hz)',
                'widget': SpinBox(
                    value=1000, 
                    bounds=(1e-6, 10e4), 
                    dec=True),
            },
            'num_samples': {
                'display_text': 'Number of MW Switches per freq per iteration',
                'widget': SpinBox(
                    value=100,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            'cooling_delay' : {
                'display_text':'Insert cooling delay?',
                'widget': QtWidgets.QCheckBox()
            },
            'duty_cycle': {
                'display_text': 'Cooling Duty Cycle (50percent if off)',
                'widget': SpinBox(
                    value=50,
                    int=False, 
                    bounds=(0, 100), 
                    dec=True),
            },
            'record_power' : {
                'display_text':'Record Power?',
                'widget': QtWidgets.QCheckBox()
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
                'widget' : QtWidgets.QLineEdit('E8257D; ')
            },
        }
        super().__init__(params_config, 
                        module =    rosetta.experiments.cwODMR.cwODMR_EXP,
                        cls =      'cwODMRExperiment',
                        fun_name = 'cwODMRsnspdE8257DfastswitchingExperiment',
                        title=     'cwODMR with SNSPD counts and E8257d sig gen, fast switching regime')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

def process_cwODMR_data(sink: DataSink):
    """Subtract the signal from background trace and add it as a new 'diff' dataset."""
    diff = []
    percent = []
    power_normalized_diff = []
    power_normalized_percent = []
    for s,_ in enumerate(sink.datasets['signal']):
        freqs = sink.datasets['signal'][s][0]
        sig = sink.datasets['signal'][s][1]
        bg = sink.datasets['background'][s][1]
        ps = sink.datasets['power'][s][1]
        diff.append(np.stack([freqs, sig - bg]))
        percent.append(np.stack([freqs, (sig - bg)/bg*100]))
        power_normalized_diff.append(np.stack([freqs, (sig - bg)/ps]))
        power_normalized_percent.append(np.stack([freqs, (sig - bg)/ps/bg*100]))
    sink.datasets['diff'] = diff
    sink.datasets['percent'] = percent
    sink.datasets['diff_power_norm'] = power_normalized_diff
    sink.datasets['percent_power_norm'] = power_normalized_percent

class FlexLinePlotWidgetWithcwODMRDefaults(FlexLinePlotWidget):
    """Add some default settings to the FlexSinkLinePlotWidget."""
    def __init__(self):
        super().__init__(data_processing_func=process_cwODMR_data)
        # create some default signal plots
        self.add_plot('sig_avg',        series='signal',   scan_i='',     scan_j='',  processing='Average')
        self.add_plot('sig_latest',     series='signal',   scan_i='-1',   scan_j='',  processing='Average')
        self.add_plot('sig_first',      series='signal',   scan_i='0',    scan_j='1', processing='Average')
        self.add_plot('sig_latest_10',  series='signal',   scan_i='-10',  scan_j='',  processing='Average')
        self.hide_plot('sig_first')
        self.hide_plot('sig_latest_10')
        self.hide_plot('sig_latest')

        # create some default background plots
        self.add_plot('bg_avg',         series='background',   scan_i='',     scan_j='',  processing='Average')
        self.add_plot('bg_latest',      series='background',   scan_i='-1',   scan_j='',  processing='Average')
        self.hide_plot('sig_latest')
        self.hide_plot('bg_latest')

        # create some default diff plots
        self.add_plot('diff_avg',       series='diff',  scan_i='',      scan_j='',  processing='Average')
        self.add_plot('diff_latest',    series='diff',  scan_i='-1',    scan_j='',  processing='Average')
        self.hide_plot('diff_latest')
        self.add_plot('percent_contrast',series='percent',scan_i='',    scan_j='',  processing='Average')
        self.add_plot('diff_avg_power_norm',       series='diff_power_norm', scan_i='', scan_j='', processing='Average')
        self.add_plot('percent_contrast_power_norm',       series='percent_power_norm', scan_i='', scan_j='', processing='Average')
        self.hide_plot('diff_avg_power_norm')
        self.hide_plot('percent_contrast_power_norm')


        # create a plot for mw power

        # manually set the XY range
        #self.line_plot.plot_item().setXRange(3000, 4000)
        #self.line_plot.plot_item().setYRange(-3000, 4500)

        # retrieve legend object
        legend = self.line_plot.plot_widget.addLegend()
        # set the legend location
        legend.setOffset((-10, -50))

        self.datasource_lineedit.setText('cwODMRsnspd')
