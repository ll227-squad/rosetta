import numpy as np
import time

import nidaqmx
from nidaqmx.stream_readers import CounterReader
from nidaqmx.constants import Edge, TriggerType, TaskMode, AcquisitionType, READ_ALL_AVAILABLE
from contextlib import ExitStack

import logging
from pathlib import Path
from itertools import count
from nspyre import nspyre_init_logger
from nspyre import StreamingList, DataSource, experiment_widget_process_queue

from rosetta.insmgr import MyInstrumentManager
from rpyc.utils.classic import obtain

from pulsestreamer import PulseStreamer

num_samples = 20

read_tasks = []
reader_streams = []
start_time = time.time()
all_counts = [] 
ctrTasks = []

ps = PulseStreamer('192.168.1.105')
print(ps.getSerial())
rabiSeq = ps.createSequence()

"""
#clk_width = 1000
rabiSeq.setDigital(2,[(1800000,1),[1800000,0]])
rabiSeq.setDigital(3,[(500000+100000+500000+100000+10000,0),(10000,1),(500000-40000,0),(10000,1),(10000+100000+500000+700000+10000,0),(10000,1),(500000-40000,0),(10000,1),(10000+100000,0)])
rabiSeq.setDigital(4,[(500000,1),(700000,0),(500000,1),(100000,0),(500000,1),(700000,0),(500000,1),(100000,0)])
rabiSeq.setDigital(4,[(3600000,1)])

laser_power=1
mw_power=-50
mw_frequency=1355
t_init=500000 #us
t_mw_delay=100000 #us
t_rabi_min=500000 #us
t_rabi_max=600000 #us
num_points = 2 # how many taus
iterations =1, # how many times to repeat measurement at each tau
t_readout_delay = 100000 #us
t_readout = 500000 #us
num_samples = 5*4 # how many averages to perform at each tau in one iteration
clk_width = 10000 #us, width of clk pulses--keep constant 
clk_buffer = 10000 #us, buffer on each side of t_readout where clk is pushed inside readout window
daq_cts_channel = "/Dev1/PFI1"
daq_trig_channel = "/Dev1/PFI2"
daq_clk_channel = "/Dev1/PFI3"
ps_EN_channel = 0
ps_CTRL_channel = 1
ps_trig_channel = 2
ps_clk_channel = 3
ps_aom_channel = 4
#rabiSeq = ps.createSequence()
tau = t_rabi_min#tau = t_rabi_min.item() # convert numpy.float64() to Python float object

patt0 = [(t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau,0),
         (t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau,0)]

patt1 = [(t_init+t_mw_delay,0),(tau,1),(t_readout_delay+t_readout+t_rabi_max-tau,0),
         (t_init+t_mw_delay,0),(tau,0),(t_readout_delay+t_readout+t_rabi_max-tau,0)]

patt2 = [(clk_buffer,0),(clk_width,1),(t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau-clk_buffer-clk_width,0),
         (clk_buffer,0),(clk_width,0),(t_init+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau-clk_buffer-clk_width,0)]

patt3 = [(t_init+t_mw_delay+tau+t_readout_delay+clk_buffer,0),(clk_width,1),(t_readout-clk_width-clk_width-clk_buffer-clk_buffer,0),(clk_width,1),(clk_buffer+t_rabi_max-tau,0),
         (t_init+t_mw_delay+tau+t_readout_delay+clk_buffer,0),(clk_width,1),(t_readout-clk_width-clk_width-clk_buffer-clk_buffer,0),(clk_width,1),(clk_buffer+t_rabi_max-tau,0)]

patt4 = [(t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_readout,1),(t_rabi_max-tau,0),
         (t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_readout,1),(t_rabi_max-tau,0)]

rabiSeq.setDigital(ps_EN_channel, patt0)
rabiSeq.setDigital(ps_CTRL_channel, patt1)
rabiSeq.setDigital(ps_trig_channel, patt2)
rabiSeq.setDigital(ps_clk_channel, patt3)
rabiSeq.setDigital(ps_aom_channel, patt4)

"""

t0 = 0e6
t1 = 20e6
dt1 = 10e6
dt2 = 20e6
clk_width = dt1/2
total = 60e6
delay = 20e6

num_samples = 50
# daq trigger (for convenience)
patt0 = [(clk_width,1),(total-clk_width,0)]
# aom
patt2 = [(t1,1),(dt1,0),(total-t1-dt1,1)]
# photon read
patt1 = [(delay,0),(clk_width,1),(dt1-clk_width,0),(clk_width,1),(total-delay-clk_width-dt1,0)]

rabiSeq.setDigital(0, [(total,0)])
rabiSeq.setDigital(1, [(total,0)])
rabiSeq.setDigital(2, patt0)
rabiSeq.setDigital(3, patt1)
rabiSeq.setDigital(4, patt2)

ps.stream(rabiSeq)
rabiSeq.plot()

if len(read_tasks) != 0:  # in case the DAQ object was killed before the reading was over, close and destroy all read tasks
    for read_task, reader_stream in zip(read_tasks, reader_streams):
        # print('in if')
        read_task.stop()
        read_task.close()
        read_tasks.remove(read_task)
        reader_streams.remove(reader_stream)

with nidaqmx.Task() as ctrTask:
    read_tasks.append(ctrTask)
    ctrTask.ci_channels.add_ci_count_edges_chan('/Dev1/ctr0')
    ctrTask.ci_channels.all.ci_count_edges_term = '/Dev1/PFI1'
    ctrTask.timing.cfg_samp_clk_timing(
                                                    20e6,       # minimum time bin that DAQ will expect from source
                                        source ='/Dev1/PFI3', # TTL pulses from Swabian telling when to create new time bin on ctr0
                                        active_edge = nidaqmx.constants.Edge.RISING,
                                        sample_mode = nidaqmx.constants.AcquisitionType.FINITE,
                                        samps_per_chan = num_samples # number of TTL pulses to expect from Swabian
    )

    ctrTask.triggers.arm_start_trigger.trig_type = TriggerType.DIGITAL_EDGE
    ctrTask.triggers.arm_start_trigger.dig_edge_edge = Edge.RISING
    ctrTask.triggers.arm_start_trigger.dig_edge_src = '/Dev1/PFI2'
    #ctrTask.control(TaskMode.TASK_COMMIT)

    reader_streams.append(nidaqmx.stream_readers.CounterReader(ctrTask.in_stream))
    ctrTasks.append(ctrTask)

    ctrTask.start()
    #print('start')

    for readerStream in reader_streams:
        ctrRawCts = np.zeros(num_samples, dtype=np.uint32)
        t0 = time.time()
        # Read counts out of the buffer
        readerStream.read_many_sample_uint32(ctrRawCts,
                                                number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE,
                                                timeout = 30)#s overhead
        t1 = time.time()
        # calculate the difference in counts between each sampling period
        all_counts.append(np.diff(ctrRawCts))
        #all_counts.append(ctrRawCts)

    ctrTask.control(TaskMode.TASK_STOP)
    ctrTask.control(TaskMode.TASK_UNRESERVE)
    #ctrTask.stop()
    #ctrTask.close()

    #print(ctrRawCts)
    print(t1-t0)
    print(np.array(all_counts).tolist())
    data = np.array(all_counts).tolist()
    signal = data[0][0::4]
    background = data[0][2::4]
    print(signal)
    print(background)
