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