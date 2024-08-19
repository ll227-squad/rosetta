#!/usr/bin/env python
"""
Start up an instrument server to host drivers. For the purposes of this demo,
it's assumed that this is running on the same system that will run experimental
code.
"""
from pathlib import Path
import logging

from nspyre import InstrumentServer
from nspyre import InstrumentGateway
from nspyre import nspyre_init_logger
from nspyre import serve_instrument_server_cli

_HERE = Path(__file__).parent

# log to the console as well as a file inside the logs folder
nspyre_init_logger(
    logging.INFO,
    log_path=_HERE / 'logs',
    log_path_level=logging.DEBUG,
    prefix='inserv_primary',
    file_size=10_000_000,
)

with InstrumentServer() as inserv_primary:#, InstrumentGateway() as remote_gw:
    ################################################################################
    #################### ADD DRIVERS TO PRIMARY INSERV HERE ########################
    ################################################################################

    # Method: add(name, class_path, class_name, args=None, kwargs=None, import_or_file='file', local_args=False)
    # name (str): Alias for the device
    # class_path (str): Driver file path (_HERE / 'drivers' /'driver.py') 
    # class_name (str): Name of the class in the driver file that instantiates the instrument (PS100, e.g.)
    # args (list, optional): Arguments to pass to class_name.__init__
    # kwargs (Dict, optional): Keyword arguments to pass to class_name.__init__
    # import_or_file (str, optional): 'import' for creating the device instance from a python module
    #                                 'file' for creating the device instance from a file in the local library
    # local_args (bool, optional): True if all arguments to this method are assumed to be local variables not passed through an instrument gateway
    #                              False if not; all arguments passed through rpyc to make sure there are no netref types


    #inserv_primary.add('subs',              _HERE /  'drivers' / 'driver_subsystems.py'             , 'SubsystemsDriver'    , args=[inserv_primary, remote_gw], local_args=True)
    inserv_primary.add('odmr_driver',       _HERE /  'drivers' / 'driver_fake_odmr.py'              , 'FakeODMRInstrument'  , args=[])
    #inserv_primary.add('powerMeter_driver', _HERE /  'drivers' / 'thorlabs' / 'PM100USB.py'         , 'PM100USBInstrument'  , args=['USB0::0x1313::0x8072::1916964::INSTR'])
    inserv_primary.add('ni_photonCounting', _HERE /  'drivers' / 'ni'       / 'ni_photonCounting.py', 'nidaqPhotonCounter'  , args=[])
    inserv_primary.add('ni_motionControl',  _HERE /  'drivers' / 'ni'       / 'ni_motionControl.py' , 'nidaqMotionControl'  , args=[])
    #inserv_primary.add('cwave_driver',      _HERE /  'drivers' / 'hubner'   / 'gtr.py'              , 'Gtr'                 , args=[])

    ################################################################################
    ################################################################################
    ################################################################################

    # run a CLI (command-line interface) that allows the user to enter
    # commands to control the server
    serve_instrument_server_cli(inserv_primary)
