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

import rosetta.experiments.rabi.rabi_EXP

class rabiDiffWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('rabiDiff')
            },
            'laser_power': {
                'display_text': 'Laser Power (Vaom)',
                'widget': SpinBox(
                    value=1, 
                    bounds=(0, 1), 
                    dec=True),
            },
             'mw_power': {
                'display_text': 'MW Power (dBm)',
                'widget': SpinBox(
                    value=-40, 
                    bounds=(-60, 4), 
                    dec=True),
            },
            'mw_frequency': {
                'display_text': 'Frequency (MHz)',
                'widget': SpinBox(
                    value=1.352626e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
                    dec=True,
                ),
            },
            't_aom_delay': {
                'display_text': 'AOM Delay (us)',
                'widget': SpinBox(
                    value=1.073, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_init': {
                'display_text': 'Initialization Time (us)',
                'widget': SpinBox(
                    value=1000, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_mw_delay': {
                'display_text': 'Delay Before MWs (us)',
                'widget': SpinBox(
                    value=0.01, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_rabi_min': {
                'display_text': 'Minimum Tau (us)',
                'widget': SpinBox(
                    value=0.01, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_rabi_max': {
                'display_text': 'Maximum Tau (us)',
                'widget': SpinBox(
                    value=0.51, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            'num_points': {
                'display_text': 'Number of Points (Taus)',
                'widget': SpinBox(
                    value=101,
                    int=True, 
                    bounds=(2, 10e3), 
                    dec=True),
            },
            'iterations': {
                'display_text': 'Number of Experiment Repeats',
                'widget': SpinBox(
                    value=1,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            't_readout_delay': {
                'display_text': 'Delay Before Readout (us)',
                'widget': SpinBox(
                    value=0.01, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_readout': {
                'display_text': 'Readout Time (us)',
                'widget': SpinBox(
                    value=0.75, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            'num_samples': {
                'display_text': 'Avgs per Tau per Iteration',
                'widget': SpinBox(
                    value=1000,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            'clk_width': {
                'display_text': 'Clock Pulse Width (us)',
                'widget': SpinBox(
                    value=10, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            'clk_buffer': {
                'display_text': 'Clock Pulse Margin (us)',
                'widget': SpinBox(
                    value=10, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
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
                'widget' : QtWidgets.QLineEdit()
            },
        }
        super().__init__(params_config, 
                        module =    rosetta.experiments.rabi.rabi_EXP,
                        cls =      'rabiExperiment',
                        fun_name = 'rabiDiffExperiment',
                        title=     'Rabi with SNSPD counts')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

class rabiAbbrWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('rabiAbbr')
            },
            'laser_power': {
                'display_text': 'Laser Power (Vaom)',
                'widget': SpinBox(
                    value=1, 
                    bounds=(0, 1), 
                    dec=True),
            },
             'mw_power': {
                'display_text': 'MW Power (dBm)',
                'widget': SpinBox(
                    value=-40, 
                    bounds=(-60, 4), 
                    dec=True),
            },
            'mw_frequency': {
                'display_text': 'Frequency (MHz)',
                'widget': SpinBox(
                    value=1.352626e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
                    dec=True,
                ),
            },
            't_aom_delay': {
                'display_text': 'AOM Delay (us)',
                'widget': SpinBox(
                    value=1.073, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_init': {
                'display_text': 'Initialization Time (us)',
                'widget': SpinBox(
                    value=1000, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_mw_delay': {
                'display_text': 'Delay Before MWs (us)',
                'widget': SpinBox(
                    value=0.01, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_rabi_min': {
                'display_text': 'Minimum Tau (us)',
                'widget': SpinBox(
                    value=0.01, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_rabi_max': {
                'display_text': 'Maximum Tau (us)',
                'widget': SpinBox(
                    value=0.51, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            'num_points': {
                'display_text': 'Number of Points (Taus)',
                'widget': SpinBox(
                    value=101,
                    int=True, 
                    bounds=(2, 10e3), 
                    dec=True),
            },
            'iterations': {
                'display_text': 'Number of Experiment Repeats',
                'widget': SpinBox(
                    value=1,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            't_readout_delay': {
                'display_text': 'Delay Before Readout (us)',
                'widget': SpinBox(
                    value=0.01, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            't_readout': {
                'display_text': 'Readout Time (us)',
                'widget': SpinBox(
                    value=0.75, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            'num_samples': {
                'display_text': 'Avgs per Tau per Iteration',
                'widget': SpinBox(
                    value=1000,
                    int=True, 
                    bounds=(1, 10e3), 
                    dec=True),
            },
            'clk_width': {
                'display_text': 'Clock Pulse Width (us)',
                'widget': SpinBox(
                    value=10, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            'clk_buffer': {
                'display_text': 'Clock Pulse Margin (us)',
                'widget': SpinBox(
                    value=60, 
                    suffix='us',
                    bounds=(1e-6, 1e9), 
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
                'widget' : QtWidgets.QLineEdit()
            },
        }
        super().__init__(params_config, 
                        module =    rosetta.experiments.rabi.rabi_EXP,
                        cls =      'rabiExperiment',
                        fun_name = 'rabiAbbrExperiment',
                        title=     'Abbreviated Rabi with SNSPD counts')
        
        """Args for super (parent class) init function:
        
        params_config: dictionary that is passed tot he constructor of ParamsWidget
        module(types.ModuleType): Python module that contains cls
        cls (str): Python class name as a string. An instance of this class will be created in a subprocess when the user presses the 'Run' button.
        fun_name (str): name of the function within cls to run. All the values from the ParamsWidget will be passed as keyword arguments to this function
        title (str, optional): Window title"""

def process_rabiDiff_data(sink: DataSink):
    """Subtract the signal from background trace and add it as a new 'diff' dataset."""
    diff = []
    percent = []
    for s,_ in enumerate(sink.datasets['signal']):
        freqs = sink.datasets['signal'][s][0]
        sig = sink.datasets['signal'][s][1]
        bg = sink.datasets['background'][s][1]
        diff.append(np.stack([freqs, sig - bg]))
        percent.append(np.stack([freqs, (sig - bg)/bg*100]))
    sink.datasets['diff'] = diff
    sink.datasets['percent'] = percent

class FlexLinePlotWidgetWithRabiDefaults(FlexLinePlotWidget):
    """Add some default settings to the FlexSinkLinePlotWidget."""
    def __init__(self):
        super().__init__(data_processing_func=process_rabiDiff_data)
        # create some default signal plots
        self.add_plot('sig_avg',        series='signal',   scan_i='',     scan_j='',  processing='Average')
        self.add_plot('sig_latest',     series='signal',   scan_i='-1',   scan_j='',  processing='Average')
        self.add_plot('sig_first',      series='signal',   scan_i='0',    scan_j='1', processing='Average')
        self.add_plot('sig_latest_10',  series='signal',   scan_i='-10',  scan_j='',  processing='Average')
        self.hide_plot('sig_first')
        self.hide_plot('sig_latest_10')

        # create some default background plots
        self.add_plot('bg_avg',         series='background',   scan_i='',     scan_j='',  processing='Average')
        self.add_plot('bg_latest',      series='background',   scan_i='-1',   scan_j='',  processing='Average')

        # create some default diff plots
        self.add_plot('diff_avg',       series='diff',  scan_i='',      scan_j='',  processing='Average')
        self.add_plot('diff_latest',    series='diff',  scan_i='-1',    scan_j='',  processing='Average')
        self.add_plot('percent_contrast',series='percent',scan_i='',    scan_j='',  processing='Average')


        # manually set the XY range
        #self.line_plot.plot_item().setXRange(3000, 4000)
        #self.line_plot.plot_item().setYRange(-3000, 4500)

        # retrieve legend object
        legend = self.line_plot.plot_widget.addLegend()
        # set the legend location
        legend.setOffset((-10, -50))

        self.datasource_lineedit.setText('rabiDiff')