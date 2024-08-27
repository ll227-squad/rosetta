from pathlib import Path
import logging

from nspyre import InstrumentServer
from nspyre import serve_instrument_server_cli
from nspyre import nspyre_init_logger

_HERE = Path(__file__).parent

# log to console and to file in "logs" folder
nspyre_init_logger(
    logging.INFO,
    log_path=_HERE / 'logs',
    prefix='inserv_cwave',
    file_size=10_000_000,
)

with InstrumentServer(port=42057) as inserv_cwave:
    inserv_cwave.add('cwave_driver', _HERE / 'drivers' / 'hubner' / 'gtr_wrapper.py'  , 'Gtr_wrapper')
    serve_instrument_server_cli(inserv_cwave)