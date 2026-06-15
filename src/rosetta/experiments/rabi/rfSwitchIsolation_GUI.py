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

import rosetta.experiments.rabi.rfSwitchIsolation_EXP

class rfSwitchIsolationWidget(ExperimentWidget):
    def __init__(self):
        params_config = {
            'dataset' : {
                'display_text' : 'Dataset Name',
                'widget' : QtWidgets.QLineEdit('rfSwitchIsolation')
            },
             'mw_power': {
                'display_text': 'MW Power (dBm)',
                'widget': SpinBox(
                    value=-40, 
                    bounds=(-60, 4), 
                    dec=True),
            },
            'mw_freq': {
                'display_text': 'Frequency (MHz)',
                'widget': SpinBox(
                    value=2e3,
                    suffix='MHz',
                    #siPrefix=True,
                    bounds=(10e-3, 40e3),
                    dec=True,
                ),
            },
            'rate': {
                'display_text': 'Rate (Hz)',
                'widget': SpinBox(
                    value=2, 
                    suffix='Hz',
                    bounds=(1e-6, 1e9), 
                    dec=True),
            },
            'daq_sd_channel' : {
                'display_text': 'DAQ AI Channel for Schottky Diode',
                'widget': QtWidgets.QLineEdit('Dev1/AI0')
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
            'comments' : {
                'display_text' : 'Comments',
                'widget' : QtWidgets.QLineEdit()
            },
        }

        super().__init__(params_config, 
                        module =    rosetta.experiments.rabi.rfSwitchIsolation_EXP,
                        cls =      'rfSwitchIsolationExperiment',
                        fun_name = 'rfSwitchIsolationExperiment',
                        title=     'Check rf switch isolation')