#!/usr/bin/env python
"""
This is an example script that demonstrates the basic functionality of nspyre.
"""
import logging
from pathlib import Path

import nspyre.gui.widgets.save
import nspyre.gui.widgets.load
import nspyre.gui.widgets.flex_line_plot
import nspyre.gui.widgets.subsystem
from nspyre import MainWidget
from nspyre import MainWidgetItem
from nspyre import nspyre_init_logger
from nspyre import nspyreApp

# in order for dynamic reloading of code to work, you must pass the specifc
# module containing your class to MainWidgetItem, since the python reload()
# function does not recursively reload modules
import rosetta.gui.elements
from rosetta.insmgr import MyInstrumentManager

###########################################################################
######################## Import GUI files here ############################
###########################################################################

import rosetta.experiments.TaskVsTime.TaskVsTime_GUI
import rosetta.experiments.fsmScan.fsmScan_GUI
import rosetta.experiments.cwODMR.cwODMR_GUI
import rosetta.experiments.cwODMR.signalGenerator_GUI
import rosetta.experiments.pODMR.pODMR_GUI
import rosetta.experiments.rabi.rabi_GUI
import rosetta.experiments.rabi.aomDelay_GUI
import rosetta.experiments.rabi.rfSwitchIsolation_GUI
import rosetta.experiments.t2Ramsey.t2Ramsey_GUI
import rosetta.experiments.t2Hahn.t2Hahn_GUI
import rosetta.experiments.t1.t1_GUI

import rosetta.experiments.powerMeter.powerMeter_GUI
import rosetta.experiments.cwave.cwave_GUI
import rosetta.experiments.eom.eom_GUI

###########################################################################
###########################################################################
###########################################################################

_HERE = Path(__file__).parent

def main():
    # Log to the console as well as a file inside the logs folder.
    nspyre_init_logger(
        log_level=logging.INFO,
        log_path=_HERE / '../logs',
        log_path_level=logging.DEBUG,
        prefix=Path(__file__).stem,
        file_size=10_000_000,
    )

    with MyInstrumentManager() as insmgr:
        # Create Qt application and apply nspyre visual settings.
        app = nspyreApp()

        # Create the GUI.
        main_widget = MainWidget(
            {
                ###########################################################################
                ######################### Add widgets to app here #########################
                ###########################################################################

                'Task Vs Time': {
                    'Task Vs Time': MainWidgetItem(rosetta.experiments.TaskVsTime.TaskVsTime_GUI, 'taskVsTimeWidget', stretch=(1, 1)), 
                    'Task Vs Time Plot': MainWidgetItem(rosetta.experiments.TaskVsTime.TaskVsTime_GUI, 'FlexLinePlotWidgetWithTVTDefaults', stretch=(1, 1)),
                    'AI Vs AO': MainWidgetItem(rosetta.experiments.TaskVsTime.TaskVsTime_GUI, 'aoaiVsTimeWidget', stretch=(1, 1)), 
                    'AI Vs Time Plot': MainWidgetItem(rosetta.experiments.TaskVsTime.TaskVsTime_GUI, 'FlexLinePlotWidgetWithAOAIVTDefaults', stretch=(1, 1)), 
                    },

                'Optical Power' : {
                    'Power Meter': MainWidgetItem(rosetta.experiments.powerMeter.powerMeter_GUI, 'powerMeterWidget',stretch=(1,1)),
                    'Power Meter Plot' : MainWidgetItem(rosetta.experiments.powerMeter.powerMeter_GUI,'FlexLinePlotWidgetWithPVTDefaults',stretch=(1,1))
                    },

                'Signal Generator' : {
                    'Signal Generator Status': MainWidgetItem(rosetta.experiments.cwODMR.signalGenerator_GUI, 'signalGeneratorStatusWidget',stretch=(1,1)),
                    'Signal Generator Trace': MainWidgetItem(rosetta.experiments.cwODMR.signalGenerator_GUI, 'signalGeneratorWidget',stretch=(1,1)),
                    'Signal Generator Plot' : MainWidgetItem(rosetta.experiments.cwODMR.signalGenerator_GUI,'FlexLinePlotWidgetWithFVTDefaults',stretch=(1,1))
                    },

                'Calibration' : {
                    'Schottky Diode mVoltage': MainWidgetItem(rosetta.experiments.cwODMR.cwODMR_GUI, 'mwPowerWidget',stretch=(1,1)),
                    'Schottky Diode mVoltage Plot' : MainWidgetItem(rosetta.experiments.cwODMR.cwODMR_GUI,'FlexLinePlotWidgetWithPVTDefaults',stretch=(1,1)),
                    'AOM Delay' : MainWidgetItem(rosetta.experiments.rabi.aomDelay_GUI, 'aomDelayWidget', stretch=(1,1)),
                    'AOM Delay Plot' :MainWidgetItem(rosetta.experiments.rabi.aomDelay_GUI,'FlexLinePlotWidgetWithAOMDelayDefaults',stretch=(1,1)),
                    'rf Switch Isolation' : MainWidgetItem(rosetta.experiments.rabi.rfSwitchIsolation_GUI, 'rfSwitchIsolationWidget', stretch=(1,1))
                    },

                'C-WAVE Output Power' : {
                    'Trace': MainWidgetItem(rosetta.experiments.cwave.cwave_GUI, 'cwaveTraceWidget',stretch=(1,1)),
                    'C-WAVE Output Power Plot' : MainWidgetItem(rosetta.experiments.cwave.cwave_GUI,'FlexLinePlotWidgetWithCWAVEVTDefaults',stretch=(1,1))
                    },

                'FSM': {
                    'FSM Scan': MainWidgetItem(rosetta.experiments.fsmScan.fsmScan_GUI, 'fsmScanWidget', stretch=(1, 1)),
                    'FSM Scan Image': MainWidgetItem(rosetta.experiments.fsmScan.fsmScan_GUI, 'fsmScanPlotWidget', stretch=(100, 100), ),
                    'FSM Move': MainWidgetItem(rosetta.experiments.fsmScan.fsmScan_GUI, 'fsmMoveWidget', stretch=(1,1))
                    },

                'C-WAVE PLE'  : {
                    'C-WAVE PLE': MainWidgetItem(rosetta.experiments.cwave.cwave_GUI, 'cwavePLEWidget', stretch=(1, 1)),
                    'C-WAVE PLE Plot': MainWidgetItem(rosetta.experiments.cwave.cwave_GUI, 'FlexLinePlotWidgetWithCWAVEPLEDefaults',stretch=(1,1)),
                    'C-WAVE PLE with lock': MainWidgetItem(rosetta.experiments.cwave.cwave_GUI, 'cwavePLElockedWidget', stretch=(1, 1)),
                    'C-WAVE PLE with lock Plot': MainWidgetItem(rosetta.experiments.cwave.cwave_GUI, 'FlexLinePlotWidgetWithCWAVEPLElockedDefaults',stretch=(1,1))
                    },

                'CW ODMR' : {
                    'CW ODMR femto': MainWidgetItem(rosetta.experiments.cwODMR.cwODMR_GUI, 'cwODMRfemtoWidget', stretch=(1, 1)),
                    'CW ODMR snspd': MainWidgetItem(rosetta.experiments.cwODMR.cwODMR_GUI, 'cwODMRsnspdWidget', stretch=(1, 1)),
                    'CW ODMR snspd E8257D': MainWidgetItem(rosetta.experiments.cwODMR.cwODMR_GUI, 'cwODMRsnspdE8257DWidget', stretch=(1, 1)),
                    'CW ODMR snspd E8257D control duty cycle': MainWidgetItem(rosetta.experiments.cwODMR.cwODMR_GUI, 'cwODMRsnspdE8257DdutycycleWidget', stretch=(1, 1)),
                    'CW ODMR snspd E8257D fast switching': MainWidgetItem(rosetta.experiments.cwODMR.cwODMR_GUI, 'cwODMRsnspdE8257DfastswitchingWidget', stretch=(1, 1)),
                    'CW ODMR Plot': MainWidgetItem(rosetta.experiments.cwODMR.cwODMR_GUI, 'FlexLinePlotWidgetWithcwODMRDefaults',stretch=(1,1))
                    },

                'Rabi' : {
                    'Rabi Differential': MainWidgetItem(rosetta.experiments.rabi.rabi_GUI, 'rabiDiffWidget', stretch=(1, 1)),
                    'Rabi Abbreviated': MainWidgetItem(rosetta.experiments.rabi.rabi_GUI, 'rabiAbbrWidget', stretch=(1, 1)),
                    'Rabi Plot': MainWidgetItem(rosetta.experiments.rabi.rabi_GUI, 'FlexLinePlotWidgetWithRabiDefaults',stretch=(1,1))
                    },

                'Pulsed ODMR':{
                    'pODMR': MainWidgetItem(rosetta.experiments.pODMR.pODMR_GUI, 'pODMRWidget', stretch=(1, 1)),
                    'pODMR abbr sequence': MainWidgetItem(rosetta.experiments.pODMR.pODMR_GUI, 'pODMRabbrWidget', stretch = (1,1)),
                    'pODMR absolute sequence': MainWidgetItem(rosetta.experiments.pODMR.pODMR_GUI, 'pODMRabsoluteWidget', stretch = (1,1)),
                    'pODMR Plot': MainWidgetItem(rosetta.experiments.pODMR.pODMR_GUI, 'FlexLinePlotWidgetWithpODMRDefaults', stretch=(1, 1)), 
                    },

                'T1':{
                    'T1': MainWidgetItem(rosetta.experiments.t1.t1_GUI, 't1Widget', stretch=(1, 1)),
                    'T1 with Pi Pulse': MainWidgetItem(rosetta.experiments.t1.t1_GUI, 't1PiWidget', stretch=(1, 1)),
                    'T1 Plot': MainWidgetItem(rosetta.experiments.t1.t1_GUI, 'FlexLinePlotWidgetWitht1Defaults', stretch=(1, 1)), 
                    },

                'T2 Ramsey':{
                    'T2 Ramsey': MainWidgetItem(rosetta.experiments.t2Ramsey.t2Ramsey_GUI, 't2RamseyWidget', stretch=(1, 1)),
                    'T2 Ramsey Plot': MainWidgetItem(rosetta.experiments.t2Ramsey.t2Ramsey_GUI, 'FlexLinePlotWidgetWitht2Defaults', stretch=(1, 1)), 
                    },

                'T2 Hahn':{
                    'T2 Hahn Freq Domain': MainWidgetItem(rosetta.experiments.t2Hahn.t2Hahn_GUI, 't2HahnFreqDomainWidget', stretch=(1, 1)),
                    'T2 Hahn Plot': MainWidgetItem(rosetta.experiments.t2Hahn.t2Hahn_GUI, 'FlexLinePlotWidgetWitht2HahnDefaults', stretch=(1, 1)), 
                    },

                'EOM Scans':{
                    'EOM SRS Scan': MainWidgetItem(rosetta.experiments.eom.eom_GUI, 'eomSRSWidget', stretch=(1, 1)),
                    'EOM SRS Transient Scan': MainWidgetItem(rosetta.experiments.eom.eom_GUI, 'eomSRStransientWidget', stretch=(1, 1)),
                    'EOM E8257D Scan': MainWidgetItem(rosetta.experiments.eom.eom_GUI, 'eomE8257DWidget', stretch=(1, 1)),
                    'EOM E8257D Scan with cycling MWs': MainWidgetItem(rosetta.experiments.eom.eom_GUI, 'eomE8257DwithMWcyclingWidget', stretch=(1, 1)),
                    'EOM Scan Plot': MainWidgetItem(rosetta.experiments.eom.eom_GUI, 'FlexLinePlotWidgetWithEOMScanDefaults', stretch=(1, 1)), 
                    },

                ############################# Example widgets #############################
            
                'Plots': {
                    'FlexLinePlotDemo': MainWidgetItem(
                        rosetta.gui.elements,
                        'FlexLinePlotWidgetWithODMRDefaults',
                        stretch=(100, 100),
                    ),
                    'FlexLinePlot': MainWidgetItem(
                        nspyre.gui.widgets.flex_line_plot,
                        'FlexLinePlotWidget',
                        stretch=(100, 100),
                    ),
                },

                ############################# Utility widgets #############################

                #'Subsystems': MainWidgetItem(nspyre.gui.widgets.subsystem, 'SubsystemsWidget', args=[insmgr.subs.subsystems], stretch=(1, 1)),
                'Save': MainWidgetItem(nspyre.gui.widgets.save, 'SaveWidget', stretch=(1, 1)),
                'Load': MainWidgetItem(nspyre.gui.widgets.load, 'LoadWidget', stretch=(1, 1)),

                ###########################################################################
                ###########################################################################
                ###########################################################################
            }
        )
        main_widget.show()

        # Run the GUI event loop.
        app.exec()


# if using the nspyre ProcessRunner, the main code must be guarded with if __name__ == '__main__':
# see https://docs.python.org/2/library/multiprocessing.html#windows
if __name__ == '__main__':
    main()



"""
                'Task Vs Time': {
                    'Task Vs Time Exp': MainWidgetItem(TaskVsTime_GUI, 'TaskVsTimeWidget', stretch=(1, 1)), 
                    'Task Vs Time Plot': MainWidgetItem(TaskVsTime_GUI, 'FlexLinePlotWidgetWithTVTDefaults', stretch=(1, 1)), 
                    },
                'FSM Scan': {
                    'FSM Scan Exp': MainWidgetItem(fsmScan_GUI, 'CustomFsmScanWidget', stretch=(1, 1)),
                    'FSM Scan Image': MainWidgetItem( fsmScan_GUI, 'FsmScanPlotWidget', stretch=(100, 100), ),
                    },
                'CW ODMR': {
                    'CW ODMR Exp': MainWidgetItem(cwODMR_GUI, 'CW_ODMR_Widget', stretch=(1, 1)),
                    'CW ODMR Plot': MainWidgetItem(cwODMR_GUI, 'FlexLinePlotWidgetWithCWODMRDefaults', stretch=(1, 1)), 
                    },
                'Pulsed ODMR':{
                    'PODMR Exp': MainWidgetItem(pODMR_GUI, 'P_ODMR_Widget', stretch=(1, 1)),
                    'PODMR Plot': MainWidgetItem(pODMR_GUI, 'FlexLinePlotWidgetWithPODMRDefaults', stretch=(1, 1)), 
                    },
                'Rabi': {
                    'Rabi Exp': MainWidgetItem(rabi_GUI, 'Rabi_Widget', stretch=(1, 1)),
                    'Rabi Plot': MainWidgetItem(rabi_GUI, 'FlexLinePlotWidgetWithRabiDefaults', stretch=(1, 1)), 
                    },
                'T2 Ramsey':{
                    'Ramsey Exp': MainWidgetItem(t2Ramsey_GUI, 'T2Ramsey_Widget', stretch=(1, 1)),
                    'Ramsey Plot': MainWidgetItem(t2Ramsey_GUI, 'FlexLinePlotWidgetWithT2RamseyDefaults', stretch=(1, 1)), 
                    },
                'T2 Hahn':{
                    'Hahn Exp': MainWidgetItem(t2Hahn_GUI, 'T2Hahn_Widget', stretch=(1, 1)),
                    'Hahn Plot': MainWidgetItem(t2Hahn_GUI, 'FlexLinePlotWidgetWithT2HahnDefaults', stretch=(1, 1)), 
                    },
                'T1':{
                    'T1 Exp': MainWidgetItem(t1_GUI, 'T1_Widget', stretch=(1, 1)),
                    'T1 Plot': MainWidgetItem(t1_GUI, 'FlexLinePlotWidgetWithT1Defaults', stretch=(1, 1)), 
                    },"""