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

import rosetta.experiments.cwODMR.signalGenerator_EXP

class signalGeneratorWidget(ExperimentWidget):
    def __init__(self):

        params_config = {
            'rate' : {
                'display_text': 'Sampling Rate (Hz)',
                'widget':SpinBox(
                    value=1,
                    suffix='Hz',
                    siPrefix=True,
                    bounds=(1e-3, 1e3),
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
                'widget': QtWidgets.QLineEdit('frequencyvstime')
            }
        }

        super().__init__(params_config, 
                        module =    rosetta.experiments.cwODMR.signalGenerator_EXP,
                        cls =      'signalGeneratorExperiment',
                        fun_name = 'signalGeneratorFrequencyTrace',
                        title=     'Signal Generator Frequency Trace')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

class signalGeneratorStatusWidget(ExperimentWidget):
    def __init__(self):
        params_config = {}

        super().__init__(params_config, 
                        module =    rosetta.experiments.cwODMR.signalGenerator_EXP,
                        cls =      'signalGeneratorExperiment',
                        fun_name = 'signalGeneratorStatus',
                        title=     'Get Signal Generator Status')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

        #zeroButton = QtWidgets.QPushButton('Zero')
        #zeroButton.clicked.connect()


def process_SignalGenerator_data(sink: DataSink):
    processed_dataset = []
    for s,_ in enumerate(sink.datasets['times']):
        ts = sink.datasets['times']
        fs = sink.datasets['frequencies']
        processed_dataset.append(np.stack([ts, fs]))
    sink.datasets['frequencyvstime_processed'] = processed_dataset

class FlexLinePlotWidgetWithFVTDefaults(FlexLinePlotWidget):
    """Add some default settings to the FlexSinkLinePlotWidget."""
    def __init__(self):
        super().__init__(data_processing_func = process_SignalGenerator_data)
        # create some default signal plots
        self.add_plot(name = 'frequencyvstime',
                      series='frequencyvstime_processed',
                      scan_i='',
                      scan_j='',
                      processing='Average')

        # retrieve legend object
        legend = self.line_plot.plot_widget.addLegend()
        # set the legend location
        legend.setOffset((-10, -50))

        self.datasource_lineedit.setText('frequencyvstime')