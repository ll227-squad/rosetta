import numpy as np
import time

import nidaqmx
from nidaqmx.stream_readers import CounterReader
from nidaqmx.constants import Edge, TriggerType, TaskMode, AcquisitionType, READ_ALL_AVAILABLE
from contextlib import ExitStack


class nidaqPhotonCounter():
    """
    Contains:
    - readCtrs_multi_internalClk(acqRate, numSamples, ctrChannelNums)
    - readCtrs_single_internalClk(acqRate, numSamples, ctrChannelNums)
    """
    def __init__(self):
        self.APDchannel = '/Dev1/PFI11'
        self.SNSPDchannel = '/Dev1/PFI4'
        self.SGchannel = '/Dev1/PFI1'
        self.pulseChannelsDict = {11: self.APDchannel, 
                                  4 : self.SNSPDchannel, 
                                  1 : self.SGchannel, }

    def __enter__(self):
        return self
    

    def __exit__(self, *args):
        pass

    def readCtrs_multi_internalClk(self, acqRate, numSamples:int, ctrChannelNums=[11,1]):
        """ Reads specified counter channels for a given period, a designated number of times, based on software timing (internal clock)"""

        #ctrChannels = [self.pulseChannelsDict[ctrChannelNum] for ctrChannelNum in ctrChannelNums]
        ctrChannels = [self.pulseChannelsDict[ctrChanNum] for ctrChanNum in ctrChannelNums]

        period = 1/acqRate
        numSamples += 1 # so np.diff works, and DAQ buffers must be larger than 1

        all_counts = [] # all_counts = [np.array(list of 5 samples from Counter 1), np.array(list of 5 samples from Counter 2), np.array(list of 5 samples from Counter 3)]

        # Create DAQ tasks
        with nidaqmx.Task() as beginningClkTask, ExitStack() as stack:

            # Create a started stask to begin the digital imput sample clock at an acquisition rate for clocking the counter input task
            beginningClkTask.di_channels.add_di_chan('Dev1/port0')
            beginningClkTask.timing.cfg_samp_clk_timing(acqRate, sample_mode=AcquisitionType.CONTINUOUS)
            beginningClkTask.control(TaskMode.TASK_COMMIT)

            # array containing counter read streams
            readerStreams = []
            ctrTasks = []

            # Create counter tasks
            for i, ctrChannel in enumerate(ctrChannels):

                # automatically run __enter__ and __exit__ methods as if they were used with a "with" statement
                ctrTask = stack.enter_context(nidaqmx.Task())

                # create a counter task
                ctrTask.ci_channels.add_ci_count_edges_chan(f'Dev1/ctr{i}') # Connect to a ctr
                ctrTask.ci_channels.all.ci_count_edges_term = ctrChannel       # Connect counter to relevant PFI channel

                # configure the couter input task
                ctrTask.timing.cfg_samp_clk_timing(acqRate, source='/Dev1/di/SampleClock', samps_per_chan = numSamples)  

                # create counter input stream object for later
                readerStreams.append(CounterReader(ctrTask.in_stream))

                # load tasks to be quickly run together later
                ctrTask.control(TaskMode.TASK_COMMIT) # alternative to task.start()
                #ctrTask.start()
                ctrTasks.append(ctrTask)

            # Start counter tasks
            for ctrTask in ctrTasks:
                ctrTask.start()
            
            # Start starting clock
            beginningClkTask.start()

            # Read counter tasks
            for readerStream in readerStreams:
                ctrRawCts = np.zeros(numSamples, dtype=np.uint32)

                # Read counts out of the buffer
                readerStream.read_many_sample_uint32(ctrRawCts,
                                                     number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE,
                                                     timeout = numSamples*period + 1)#s overhead
                # calculate the difference in counts between each sampling period
                all_counts.append(np.diff(ctrRawCts))

            return np.array(all_counts).tolist()
        
    def readCtrs_single_internalClk(self, acqRate, ctrChannelNums=[11,1]):
        # run readCtrs_multi_internalClk
        data = self.readCtrs_multi_internalClk(acqRate, 1, ctrChannelNums)
        data_reformed = [val[0] for val in data] # go from 2D array [[channel 11 counts],[channel 1 counts]] to [channel 11 counts, channel 1 counts]; not problematic bc each list has one data point
        return data_reformed
        
if __name__=='__main__':
    daq = nidaqPhotonCounter()
    #print(daq.readCtrs_multi_internalClk(acqRate=5,numSamples=10))
    counts = daq.readCtrs_single_internalClk(acqRate=1)
    print(counts)