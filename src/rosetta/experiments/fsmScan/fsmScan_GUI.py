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

from rosetta.experiments.fsmScan import fsmScan_EXP

class fsmScanWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('FSM Scan')

        self.params_widget = ParamsWidget({
            'x'


        })