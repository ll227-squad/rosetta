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

import rosetta.experiments.cwave.cwave_EXP

################################################################################################################
######################################## power vs time #########################################################
################################################################################################################

class cwaveTraceWidget(ExperimentWidget):
    def __init__(self):

        params_config = {
            'rate' : {
                'display_text': 'Sampling Rate (Hz)',
                'widget':SpinBox(
                    value=1,
                    suffix='Hz',
                    siPrefix=True,
                    bounds=(0, 1e3),
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
            'dataset' : {
                'display_text': 'Dataset Name',
                'widget': QtWidgets.QLineEdit('CWAVEpowervstime')
            }
        }

        super().__init__(params_config, 
                        module =    rosetta.experiments.cwave.cwave_EXP,
                        cls =      'cwaveExperiment',
                        fun_name = 'cwaveTrace',
                        title=     'C-WAVE Trace')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""


def process_CWAVE_data(sink: DataSink):
    processed_datasetOPO = []
    processed_datasetSHG = []
    processed_datasetPMP = []
    for s,_ in enumerate(sink.datasets['times']):
        ts = sink.datasets['times']
        psOPO = sink.datasets['OPO powers']
        psSHG = sink.datasets['SHG powers']
        psPMP = sink.datasets['Pump powers']
        processed_datasetOPO.append(np.stack([ts, psOPO]))
        processed_datasetSHG.append(np.stack([ts, psSHG]))
        processed_datasetPMP.append(np.stack([ts, psPMP]))
        #processed_dataset.append(np.stack([ts, psOPO, psSHG, psPMP]))
    sink.datasets['OPOpowervstime_processed'] = processed_datasetOPO
    sink.datasets['SHGpowervstime_processed'] = processed_datasetSHG
    sink.datasets['PMPpowervstime_processed'] = processed_datasetPMP

class FlexLinePlotWidgetWithCWAVEVTDefaults(FlexLinePlotWidget):
    """Add some default settings to the FlexSinkLinePlotWidget."""
    def __init__(self):
        super().__init__(data_processing_func = process_CWAVE_data)
        # create some default signal plots
        self.add_plot(name = 'OPO Power Trace',
                      series='OPOpowervstime_processed',
                      scan_i='',
                      scan_j='',
                      processing='Average')
        self.add_plot(name = 'SHG Power Trace',
                      series='SHGpowervstime_processed',
                      scan_i='',
                      scan_j='',
                      processing='Average')
        
        self.add_plot(name = 'Pump Power Trace',
                      series='PMPpowervstime_processed',
                      scan_i='',
                      scan_j='',
                      processing='Average')

        # retrieve legend object
        legend = self.line_plot.plot_widget.addLegend()
        # set the legend location
        legend.setOffset((-10, -50))

        self.datasource_lineedit.setText('CWAVEpowervstime')


################################################################################################################
############################################ PLE ###############################################################
################################################################################################################

class cwavePLEWidget(ExperimentWidget):
    def __init__(self):

        params_config = {
            'min_piezo' : {
                'display_text': 'Minimum Piezo %',
                'widget':SpinBox(
                    value=10,
                    bounds=(1, 99),
                    dec=True,
                )
            },
            'max_piezo' : {
                'display_text': 'Maximum Piezo %',
                'widget':SpinBox(
                    value=90,
                    bounds=(1, 99),
                    dec=True,
                )
            },
            'scan_rate' : {
                'display_text': 'Scan Rate of Piezo (Hz)',
                'widget':SpinBox(
                    value=0.1,
                    siPrefix=False,
                    bounds=(1e-6,1e1),
                    dec=True,
                )
            },
            'num_points' : {
                'display_text': 'Number of Points',
                'widget':SpinBox(
                    value=50,
                    siPrefix=True,
                    bounds=(1, 1e6),
                    dec=False,
                    int=True,
                )
            },
            'measure_rate' : {
                'display_text': 'Rate to Measure PLE (Hz)',
                'widget':SpinBox(
                    value=5,
                    siPrefix=True,
                    bounds=(1e-5,1e2),
                    dec=True,
                )
            },
            'data_channel' : {
                'display_text': 'PFI Channel',
                'widget': QtWidgets.QLineEdit('Dev1/PFI1')
            },
            'ctr_channel' : {
                'display_text': 'Counter Channel',
                'widget': QtWidgets.QLineEdit('Dev1/ctr0')
            },
            'sampling_rate' : {
                'display_text': 'DAQ Sampling Rate (Hz)',
                'widget':SpinBox(
                    value=20000,
                    siPrefix=True,
                    bounds=(1e0,1e5),
                    dec=True,
                )
            },
            'dataset' : {
                'display_text': 'Dataset Name',
                'widget': QtWidgets.QLineEdit('CWAVEPLE')
            },
        }

        super().__init__(params_config, 
                        module =    rosetta.experiments.cwave.cwave_EXP,
                        cls =      'cwaveExperiment',
                        fun_name = 'cwavePLE',
                        title=     'C-WAVE PLE')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

def process_CWAVEPLE_data(sink: DataSink):
    processed_dataset_time = []
    processed_dataset_wavelength = []
    processed_dataset_power = []
    processed_dataset_signal = []
    processed_dataset_normalized_signal = []
    for s,_ in enumerate(sink.datasets['Wavelength during measurement (nm)']):
        times = sink.datasets['Time of measurement (s)']
        wavelengths = sink.datasets['Wavelength during measurement (nm)']
        powers = sink.datasets['Power during measurement (W)']
        counts = sink.datasets['Counts during measurement (counts)']
        processed_dataset_time.append(np.stack([times,wavelengths])) # nm vs time
        processed_dataset_wavelength.append(np.stack([wavelengths,times])) # time vs nm
        processed_dataset_power.append(np.stack([wavelengths, powers])) # W vs nm
        processed_dataset_signal.append(np.stack([wavelengths, counts])) # counts vs nm
        # data processing for normalization
        normalized_data = [c / p for c, p in zip(counts,powers)]
        normalized_mW_data = [c * 1000 for c in normalized_data]
        processed_dataset_normalized_signal.append(np.stack([wavelengths, normalized_mW_data])) # counts per mW
    sink.datasets['wavelengthsvstime_processed'] = processed_dataset_time
    sink.datasets['countsvswavelength_processed'] = processed_dataset_signal
    sink.datasets['normalizedcountsvswavelength_processed'] = processed_dataset_normalized_signal


class FlexLinePlotWidgetWithCWAVEPLEDefaults(FlexLinePlotWidget):
    """Add some default settings to the FlexSinkLinePlotWidget."""
    def __init__(self):
        super().__init__(data_processing_func = process_CWAVEPLE_data)
        # create some default signal plots
        self.add_plot(name = 'Counts vs Wavelength',
                      series='countsvswavelength_processed',
                      scan_i='',
                      scan_j='',
                      processing='Average')
        self.add_plot(name = 'Power-Normalized Counts vs Wavelength',
                      series='normalizedcountsvswavelength_processed',
                      scan_i='',
                      scan_j='',
                      processing='Average')

        # retrieve legend object
        legend = self.line_plot.plot_widget.addLegend()
        # set the legend location
        legend.setOffset((-10, -50))

        self.datasource_lineedit.setText('CWAVEPLE')

################################################################################################################
################################################################################################################
################################################################################################################