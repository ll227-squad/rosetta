import numpy as np

from nspyre import DataSink, FlexLinePlotWidget
from nspyre import ExperimentWidget

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox
from pyqtgraph import ComboBox

import rosetta.experiments.TaskVsTime.TaskVsTime_EXP

class taskVsTimeWidget(ExperimentWidget):
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
            'record_power' : {
                'widget': QtWidgets.QCheckBox(text='Record Power?')
            },
            'laser_wavelength' : {
                'display_text': 'Laser Wavelength (nm)',
                'widget': SpinBox(
                    value=1050.28, 
                    bounds=(0, 10e3), 
                    dec=True),
            },
            'autosave' : {
                'display_text': 'Autosave?',
                'widget': QtWidgets.QLineEdit('False')
            },

            'autosave_interval' : {
                'display_text': 'Autosave Interval',
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
                'widget': QtWidgets.QLineEdit('taskvstime')
            }
        }

        super().__init__(params_config, 
                        module =    rosetta.experiments.TaskVsTime.TaskVsTime_EXP,
                        cls =      'taskVsTimeExperiment',
                        fun_name = 'taskVsTimeMeasurement',
                        title=     'Time Trace')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

def process_TaskVsTime_data(sink: DataSink):
    for i in [11,1]:
        power_normalized_count_rate = []
        power_vs_time = []
        A = [np.stack([sink.datasets['times'], np.array(sink.datasets[f'pfi{i}counts'])])]
        B = [np.stack([sink.datasets['times'], np.array(sink.datasets[f'pfi{i}counts'])/np.array(sink.datasets['optical_powers_mW'])])]
        C = [np.stack([sink.datasets['times'], np.array(sink.datasets['optical_powers_mW'])])]
        sink.datasets[f'PFI{i}CountsToPlot'] = A
        sink.datasets[f'power_normalized_count_rate_PFI{i}'] = B
        sink.datasets['power_vs_time'] = C

class FlexLinePlotWidgetWithTVTDefaults(FlexLinePlotWidget):
    """Add some default settings to the FlexSinkLinePlotWidget."""
    def __init__(self):
        super().__init__(data_processing_func = process_TaskVsTime_data)
        # create some default signal plots
        self.add_plot('PFI11/Ctr0 (All Counts)', series='PFI11CountsToPlot',   scan_i='',     scan_j='',  processing='Average')

        for i in [1]:
            self.add_plot(f'PFI{i} Counts', series=f'PFI{i}CountsToPlot',   scan_i='',     scan_j='',  processing='Average')
            self.add_plot(f'PFI{i} Counts Power Normalized', series=f'power_normalized_count_rate_PFI{i}',   scan_i='',     scan_j='',  processing='Average')
            self.hide_plot(f'PFI{i} Counts Power Normalized')
            self.add_plot('Optical Power (mW)', series='power_vs_time',   scan_i='',     scan_j='',  processing='Average')

        # retrieve legend object
        legend = self.line_plot.plot_widget.addLegend()
        # set the legend location
        legend.setOffset((-10, -50))

        self.datasource_lineedit.setText('taskvstime')

class aoaiVsTimeWidget(ExperimentWidget):
    def __init__(self):

        params_config = {
            'rate' : {
                'display_text': 'Rate (Hz)',
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
                    value=101,
                    siPrefix=True,
                    bounds=(-1, 1e6),
                    dec=False,
                )
            },
            'V_pp' : {
                'display_text': 'V_pp (V)',
                'widget':SpinBox(
                    value=1,
                    suffix='V',
                    siPrefix=True,
                    bounds=(1e-3, 20),
                    dec=True,
                )
            },
            'ao_channel' : {
                'display_text': 'AO Channel',
                'widget': QtWidgets.QLineEdit('Dev1/AO2')
            },            
            'ai_channel' : {
                'display_text': 'AI Channel',
                'widget': QtWidgets.QLineEdit('Dev1/AI4')
            },
            'dataset' : {
                'display_text': 'Dataset Name',
                'widget': QtWidgets.QLineEdit('aoaivstime')
            }
        }

        super().__init__(params_config, 
                        module =    rosetta.experiments.TaskVsTime.TaskVsTime_EXP,
                        cls =      'taskVsTimeExperiment',
                        fun_name = 'aoaiVsTimeMeasurement',
                        title=     'AI Vs AO')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

def process_AOAIVsTime_data(sink: DataSink):
    A = [np.stack([sink.datasets['times'], np.array(sink.datasets['ai_values'])])]
    B = [np.stack([sink.datasets['ao_values'], np.array(sink.datasets['ai_values'])])]
    sink.datasets['AIvstimes'] = A
    sink.datasets['AIvsAO'] = B

class FlexLinePlotWidgetWithAOAIVTDefaults(FlexLinePlotWidget):
    """Add some default settings to the FlexSinkLinePlotWidget."""
    def __init__(self):
        super().__init__(data_processing_func = process_AOAIVsTime_data)
        # create some default signal plots
        self.add_plot('AI vs Time', series='AIvstimes',   scan_i='',     scan_j='',  processing='Average')
        self.add_plot('AI vs AO', series='AIvsAO',   scan_i='',     scan_j='',  processing='Average')

        # retrieve legend object
        legend = self.line_plot.plot_widget.addLegend()
        # set the legend location
        legend.setOffset((-10, -50))

        self.datasource_lineedit.setText('aoaivstime')