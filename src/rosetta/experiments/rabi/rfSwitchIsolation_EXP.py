import time
import logging
from pathlib import Path
from itertools import count
import numpy as np
from nspyre import nspyre_init_logger
from nspyre import StreamingList, DataSource, experiment_widget_process_queue

from rosetta.insmgr import MyInstrumentManager
from rpyc.utils.classic import obtain

_HERE = Path(__file__).parent
_logger = logging.getLogger(__name__)

class rfSwitchIsolationExperiment:
    def __init__(self, queue_to_exp=None, queue_from_exp=None):
        """
        Args:
            queue_to_exp: A multiprocessing Queue object used to send messages
                to the experiment from the GUI.
            queue_from_exp: A multiprocessing Queue object used to send 
                messages to the GUI from the experiment.
        """
        self.queue_to_exp = queue_to_exp
        self.queue_from_exp = queue_from_exp

    def __enter__(self):
        """Perform experiment setup."""
        # config logging messages
        # if running a method from the GUI, it will be run in a new process
        # this logging call is necessary in order to separate log messages
        # originating in the GUI from those in the new experiment subprocess
        nspyre_init_logger(
            log_level=logging.INFO,
            log_path=_HERE / '../logs',
            log_path_level=logging.DEBUG,
            prefix=Path(__file__).stem,
            file_size=10_000_000,
        )
        _logger.info('Created rfSwitchIsolationExperiment instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed rfSwitchIsolationExperiment instance.')

    def rfSwitchIsolationExperiment(self,
                                   dataset:str,
                                   mw_freq,
                                   mw_power,
                                   rate,
                                   daq_sd_channel,
                                   ps_CTRL_channel,
                                   ps_EN_channel,
                                   comments):
        
        with MyInstrumentManager() as mgr, DataSource(dataset) as rfSwitchIsolation_data:

            daq = mgr.ni_analogTasks
            pulsestreamer = mgr.pulseStreamer_driver
            srs = mgr.srs_driver

            switch_on_mw_on_data = StreamingList()   #high
            switch_off_mw_off_data = StreamingList() #low
            switch_on_mw_off_data = StreamingList()  #low
            switch_off_mw_on_data = StreamingList()  #low

            #units
            mw_freq = mw_freq*1e6

            srs.setFreq(mw_freq)
            srs.setRfAmp(mw_power)
            srs.setRfToggle(0)

            for i in count():
                print("Iteration {}.".format(i))
                #Switch_off_mw_off
                seq = pulsestreamer.ps.createSequence()
                seq.setDigital(ps_EN_channel,[(2/rate,0)])
                seq.setDigital(ps_CTRL_channel,[(2/rate,0)])
                pulsestreamer.runSequenceInfinitely(seq)
                srs.setRfToggle(0)
                
                time.sleep(1/rate)
                current_power = daq.readAI(daq_sd_channel)
                switch_off_mw_off_data.append(current_power*1000)
                switch_off_mw_off_data.append(0*1000)
                switch_on_mw_off_data.append(0)

                #Switch_on_mw_off
                seq = pulsestreamer.ps.createSequence()
                seq.setDigital(ps_EN_channel,[(2/rate,0)])
                seq.setDigital(ps_CTRL_channel,[(2/rate,1)])
                pulsestreamer.runSequenceInfinitely(seq)
                srs.setRfToggle(0)
                
                time.sleep(1/rate)
                current_power = daq.readAI(daq_sd_channel)
                switch_on_mw_off_data.append(current_power*1000)

                #Switch_on_mw_on
                seq = pulsestreamer.ps.createSequence()
                seq.setDigital(ps_EN_channel,[(2/rate*1e9,0)])
                seq.setDigital(ps_CTRL_channel,[(2/rate*1e9,1)])
                pulsestreamer.runSequenceInfinitely(seq)
                srs.setRfToggle(1)
                
                time.sleep(1/rate)
                current_power = daq.readAI(daq_sd_channel)

                switch_on_mw_on_data.append(current_power*1000)

                #Switch_off_mw_on
                seq = pulsestreamer.ps.createSequence()
                seq.setDigital(ps_EN_channel,[(2/rate*1e9,0)])
                seq.setDigital(ps_CTRL_channel,[(2/rate*1e9,0)])
                pulsestreamer.runSequenceInfinitely(seq)
                srs.setRfToggle(1)
                
                time.sleep(1/rate)
                current_power = daq.readAI(daq_sd_channel)
                switch_off_mw_on_data.append(current_power*1000)

                switch_on_mw_on_data.updated_item(-1)
                switch_off_mw_off_data.updated_item(-1)
                switch_on_mw_off_data.updated_item(-1)
                switch_off_mw_on_data.updated_item(-1)


                rfSwitchIsolation_data.push({'params': {'mw_freq_MHz' : mw_freq,
                                            'mw_power_dBm'  : mw_power,
                                            'rate_Hz' : rate,
                                            'daq_sd_channel' : daq_sd_channel,
                                            'ps_EN_channel' : ps_EN_channel,
                                            'ps_CTRL_channel' : ps_CTRL_channel,
                                            'comments'    : comments},
                                    'title' : 'Measure AOM Delay',
                                    'xlabel' : 'Time (ns)',
                                    'ylabel' : 'Counts',
                                    'datasets':{'switch_on_mw_on' : switch_on_mw_on_data,
                                                'switch_off_mw_on' : switch_off_mw_on_data,
                                                'switch_on_mw_off' : switch_on_mw_off_data,
                                                'switch_off_mw_off' : switch_off_mw_off_data,}})
                

                if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                    # the GUI has asked us nicely to exit
                    print('Schottky mV with switch ON and microwaves ON: {:.5}mV'.format(np.average(switch_on_mw_on_data)))
                    print('Schottky mV with switch OFF and microwaves ON: {:.5}mV'.format(np.average(switch_off_mw_on_data)))
                    print('Schottky mV with switch ON and microwaves OFF: {:.5}mV'.format(np.average(switch_on_mw_off_data)))
                    print('Schottky mV with switch OFF and microwaves OFF: {:.5}mV'.format(np.average(switch_off_mw_off_data)))
                    srs.setRfToggle(0)
                    return

            # Shutdown
            mwOFF = pulsestreamer.cwODMRmwOFF(1e9)
            pulsestreamer.runSequenceInfinitely(mwOFF)
            srs.setRfToggle(0)

            print('Done with rfSwitchIsolationExperiment.')