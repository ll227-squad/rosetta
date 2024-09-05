from collections import OrderedDict
import time
import numpy as np

import nidaqmx
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from nidaqmx.stream_readers import CounterReader
from nidaqmx.constants import Edge, TriggerType, TaskMode, AcquisitionType, READ_ALL_AVAILABLE
from rpyc.utils.classic import obtain

class nidaqAnalogTasks():
    """
    Contains:
    - 
    """
    def __init__(self):
        self.DevName = "Dev1" # identify default

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def readAI(self, AI_channel):
        """
        Simple on-demand read of AI_channel ("Dev1/AI2", e.g.)
        """
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(AI_channel)
            data = task.read()
            return(data)
