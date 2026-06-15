import numpy as np
import time

from pulsestreamer import PulseStreamer

ps = PulseStreamer('192.168.1.105')
print(ps.getSerial())
seq = ps.createSequence()


######################################## Rabi ###################################################################################

laser_power = 1#Vaom
t_aom_delay = 1.073 #us
t_init=30000 #us 1000
t_mw_delay= 140 #us
tau = 0.7 #us
t_rabi_max= 6 #us 0.051
t_readout_delay = 1 #us
t_readout = 2000 #us
t_wait = 50000 #us
clk_width = t_readout/2 #us, width of clk pulses--keep constant 
bin_width = 50#us


t_aom_delay = t_aom_delay*1e3
t_init = t_init*1e3
t_mw_delay = t_mw_delay*1e3
tau = tau*1e3
t_rabi_max = t_rabi_max*1e3
t_readout_delay = t_readout_delay*1e3
t_readout = t_readout*1e3
t_wait = t_wait*1e3
clk_width = clk_width*1e3
bin_width = bin_width*1e3

delay = bin_width - (t_init+t_mw_delay+tau+t_readout_delay) % bin_width
print(delay)
delay2 = bin_width - (t_readout+t_rabi_max-tau+t_wait) % bin_width
print(delay2)

print((t_readout+t_rabi_max-tau+t_wait+delay2)/bin_width)
print((t_init+delay+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau+delay2+t_wait+t_init+delay+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau+t_wait+delay2)/bin_width)

patt0 = [(t_aom_delay+t_init+delay+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau+t_wait+delay2,0),
                     (t_init+delay+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau+t_wait+delay2,0),]

patt1 = [(t_aom_delay+t_init+delay+t_mw_delay,0),(tau,1),(t_readout_delay+t_readout+t_rabi_max-tau+t_wait+delay2,0),
                     (t_init+delay+t_mw_delay,0),(tau,0),(t_readout_delay+t_readout+t_rabi_max-tau+t_wait+delay2,0)]

patt2 = [(t_aom_delay-1000,0),(clk_width+1000,1),(t_init+delay+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau-clk_width+t_wait+delay2,0),
                                                 (t_init+delay+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau          +t_wait+delay2,0)]

#patt3 = [(t_aom_delay+t_init+t_mw_delay+tau+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_rabi_max-tau,0),
#                     (t_init+t_mw_delay+tau+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_rabi_max-tau+t_wait,0)]

patt4 = [(t_init+delay,1),(t_mw_delay+tau+t_readout_delay,0),(t_readout,1),(t_rabi_max-tau+t_wait+delay2,0),
         (t_init+delay,1),(t_mw_delay+tau+t_readout_delay,0),(t_readout,1),(t_rabi_max-tau+t_wait+delay2+t_aom_delay,0)]

patt5 = [(t_aom_delay+t_init+delay+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau+t_wait+delay2,1),
                     (t_init+delay+t_mw_delay+tau+t_readout_delay+t_readout+t_rabi_max-tau+t_wait+delay2,1),]

pattA1 = [(t_init+delay,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_readout,laser_power),(t_rabi_max-tau+t_wait+delay2,0.0),
          (t_init+delay,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_readout,laser_power),(t_rabi_max-tau+t_wait+delay2+t_aom_delay,0.0)]

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
#seq.setDigital(2, patt2) # DAQ trigger
seq.setDigital(3, patt2) # DAQ clock
seq.setDigital(4, patt4) # AOM
seq.setDigital(5, patt5) # ZASWA
seq.setDigital(6, patt2) # TT trigger
seq.setAnalog(1, pattA1) # AOM analog

#patt3 = [(t_aom_delay,0),(clk_width,1),()]
#patt4 = [(t_init,1),(t_mw_delay+tau+t_readout_delay,0)]

#pattA1 = [(t_init,1.0),(t_mw_delay+tau+t_readout_delay,0.0)]

#seq.setDigital(4, patt4) # AOM
#seq.setAnalog(1, pattA1) # AOM analog

############################################# RabiDiffAbridged ####################################################################
"""
laser_power = 1#Vaom
t_aom_delay = 1.073 #us
t_init=20000 #us
t_mw_delay= 140 #us
tau = 1 # us
t_rabi_max= 1.51 #us 0.051
t_readout_delay = 1 #us
t_readout = 500 #us
clk_width = t_readout/10 #us, width of clk pulses--keep constant 
clk_buffer = 60#us
bin_width = 20#us

t_aom_delay = t_aom_delay*1e3
t_init = t_init*1e3
t_mw_delay = t_mw_delay*1e3
tau = tau*1e3
t_rabi_max = t_rabi_max*1e3
t_readout_delay = t_readout_delay*1e3
t_readout = t_readout*1e3
clk_width = clk_width*1e3
clk_buffer = clk_buffer*1e3
bin_width = bin_width*1e3

delay = bin_width - (t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau) % bin_width

print((2*(t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau)+delay)/bin_width)
#print((t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay)/bin_width)

patt0 = [(t_aom_delay+t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                     (t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau,0)]

patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(tau,1),(t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                     (t_init+t_mw_delay,0),(tau,0),(t_readout_delay+t_init+t_rabi_max-tau,0)]

patt2 = [(t_aom_delay,0),(clk_width,1),(t_init-clk_width+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                         (clk_width,0),(t_init-clk_width+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau,0)]

patt3 = [(t_aom_delay+t_init-t_readout,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_mw_delay+tau+t_readout_delay-clk_width+clk_buffer,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-clk_buffer-t_readout-clk_width+t_rabi_max-tau+delay,0),
                     (t_init-t_readout,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_mw_delay+tau+t_readout_delay-clk_width+clk_buffer,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-clk_buffer-t_readout-clk_width+t_rabi_max-tau,0)]

patt4 = [            (t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_init+t_rabi_max-tau+delay      ,1),
                     (t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_init+t_rabi_max-tau+t_aom_delay,1)]

patt5 = [(t_aom_delay+t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,1),
                     (t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau,1)]

pattA1= [            (t_init,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_init+t_rabi_max-tau+delay      ,laser_power),
                     (t_init,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_init+t_rabi_max-tau+t_aom_delay,laser_power)]


seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(6, patt2) # DAQ trigger
seq.setDigital(3, patt3) # DAQ clock
seq.setDigital(4, patt4) # AOM
seq.setDigital(5, patt5) # ZASWA
seq.setAnalog(1, pattA1)
"""
######################################################## rabi whole sequence ###############################################################
"""
laser_power = 1#Vaom
t_aom_delay = 1.073 #us
t_init=4000 #us
t_mw_delay= 140 #us
t_rabi_min = 0.01 # us
t_rabi_max= 1.01 #us 0.051
num_points = 21
t_readout_delay = 5 #us
t_readout = 460 #us
clk_width = t_readout/10 #us, width of clk pulses--keep constant 
clk_buffer = 60#us
bin_width = 20#us

t_aom_delay = t_aom_delay*1e3
t_init = t_init*1e3
t_mw_delay = t_mw_delay*1e3
t_rabi_min = t_rabi_min*1e3
t_rabi_max = t_rabi_max*1e3
t_readout_delay = t_readout_delay*1e3
t_readout = t_readout*1e3
clk_width = clk_width*1e3
clk_buffer = clk_buffer*1e3
bin_width = bin_width*1e3

delay = bin_width - (t_init+t_mw_delay+t_readout_delay+t_init+t_rabi_max) % bin_width

print(num_points*(2*(t_init+t_mw_delay+t_readout_delay+t_init+t_rabi_max+delay))/bin_width)

seq = ps.createSequence()
seq_new = ps.createSequence()

taus = np.linspace(t_rabi_min, t_rabi_max, num_points)

print()

for i in range(num_points):
    tau = taus[i]
    if i == 0:
        patt0 = [(t_aom_delay+t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                        (t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0)]

        patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(tau,1),(t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                            (t_init+t_mw_delay,0),(tau,0),(t_readout_delay+t_init+t_rabi_max-tau+delay,0)]

        patt2 = [(t_aom_delay,0),(clk_width,1),(t_init-clk_width+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                                (clk_width,0),(t_init-clk_width+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0)]

        patt3 = [(t_aom_delay+t_init-t_readout,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_mw_delay+tau+t_readout_delay-clk_width+clk_buffer,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-clk_buffer-t_readout-clk_width+t_rabi_max-tau+delay,0),
                            (t_init-t_readout,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_mw_delay+tau+t_readout_delay-clk_width+clk_buffer,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-clk_buffer-t_readout-clk_width+t_rabi_max-tau+delay,0)]

        patt4 = [            (t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_init+t_rabi_max-tau+delay      ,1),
                            (t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_init+t_rabi_max-tau+delay,             1)]

        patt5 = [(t_aom_delay+t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,1),
                            (t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,1)]

        pattA1= [            (t_init,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_init+t_rabi_max-tau+delay      ,laser_power),
                             (t_init,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_init+t_rabi_max-tau+delay             ,laser_power)]
        
    elif i == (num_points-1):
        patt0 = [(t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                     (t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0)]

        patt1 = [(t_init+t_mw_delay,0),(tau,1),(t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                            (t_init+t_mw_delay,0),(tau,0),(t_readout_delay+t_init+t_rabi_max-tau+delay,0)]

        patt2 = [               (clk_width,0),(t_init-clk_width+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                                (clk_width,0),(t_init-clk_width+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0)]

        patt3 = [           (t_init-t_readout,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_mw_delay+tau+t_readout_delay-clk_width+clk_buffer,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-clk_buffer-t_readout-clk_width+t_rabi_max-tau+delay,0),
                            (t_init-t_readout,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_mw_delay+tau+t_readout_delay-clk_width+clk_buffer,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-clk_buffer-t_readout-clk_width+t_rabi_max-tau+delay,0)]

        patt4 = [            (t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_init+t_rabi_max-tau+delay      ,1),
                            (t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_init+t_rabi_max-tau+delay+t_aom_delay,1)]

        patt5 = [(t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,1),
                            (t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,1)]

        pattA1= [            (t_init,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_init+t_rabi_max-tau+delay      ,laser_power),
                            (t_init,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_init+t_rabi_max-tau+delay+t_aom_delay,laser_power)]
    else:
        patt0 = [(t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                     (t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0)]

        patt1 = [(t_init+t_mw_delay,0),(tau,1),(t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                            (t_init+t_mw_delay,0),(tau,0),(t_readout_delay+t_init+t_rabi_max-tau+delay,0)]

        patt2 = [(clk_width,0),(t_init-clk_width+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0),
                                (clk_width,0),(t_init-clk_width+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,0)]

        patt3 = [(t_init-t_readout,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_mw_delay+tau+t_readout_delay-clk_width+clk_buffer,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-clk_buffer-t_readout-clk_width+t_rabi_max-tau+delay,0),
                            (t_init-t_readout,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_mw_delay+tau+t_readout_delay-clk_width+clk_buffer,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-clk_buffer-t_readout-clk_width+t_rabi_max-tau+delay,0)]

        patt4 = [            (t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_init+t_rabi_max-tau+delay      ,1),
                            (t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_init+t_rabi_max-tau+delay,1)]

        patt5 = [(t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,1),
                            (t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+delay,1)]

        pattA1= [            (t_init,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_init+t_rabi_max-tau+delay      ,laser_power),
                            (t_init,laser_power),(t_mw_delay+tau+t_readout_delay,0.0),(t_init+t_rabi_max-tau+delay,laser_power)]
    seq_new.setDigital(0, patt0) # switch EN
    seq_new.setDigital(1, patt1) # switch CTRL
    seq_new.setDigital(6, patt2) # DAQ trigger
    seq_new.setDigital(3, patt3) # DAQ clock
    seq_new.setDigital(4, patt4) # AOM
    seq_new.setDigital(5, patt5) # ZASWA
    seq_new.setAnalog(1, pattA1)

    seq = seq+seq_new
"""
#################################### pODMR ################################################################################
"""
t_aom_delay = 1.11 #us
t_init=10 #us 1000
t_mw_delay=1 #us
t_rabi = 0.5 #us
num_points = 50 # how many freqs
iterations = 2 # how many times to repeat measurement at each tau
t_readout_delay = 1 #us
t_readout = 2 #us
num_samples = 10 # how many averages to perform at each tau in one iteration
clk_width = t_readout/2 #us, width of clk pulses--keep constant 


t_init = t_init*1e3
t_mw_delay = t_mw_delay*1e3
t_rabi = t_rabi*1e3
t_readout_delay = t_readout_delay*1e3
t_readout = t_readout*1e3
t_aom_delay = t_aom_delay*1e3
clk_width = clk_width*1e3

patt0 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay+t_aom_delay+t_readout+clk_width,0),
         (t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay+t_aom_delay+t_readout+clk_width,0)]

patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(t_rabi,1),(t_readout_delay+t_aom_delay+t_readout+clk_width,0),
         (t_aom_delay+t_init+t_mw_delay,0),(t_rabi,0),(t_readout_delay+t_aom_delay+t_readout+clk_width,0)]

patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+t_mw_delay+t_rabi+t_readout_delay+t_aom_delay+t_readout-t_aom_delay-clk_width+clk_width,0),
         (t_aom_delay,0),(clk_width,0),(t_init+t_mw_delay+t_rabi+t_readout_delay+t_aom_delay+t_readout-t_aom_delay-clk_width+clk_width,0)]

patt3 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay+t_aom_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),
         (t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay+t_aom_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1)]

patt4 = [(t_aom_delay+t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_aom_delay+t_readout,1),(clk_width,0),
         (t_aom_delay+t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_aom_delay+t_readout,1),(clk_width,0)]

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(2, patt2) # DAQ trigger
seq.setDigital(3, patt3) # DAQ clock
seq.setDigital(4, patt4) # AOM
"""
############################################# initializiation with mws ###########################################################
"""
t_mw = 10000000 #ns
t_buffer = 10 #ns
t_laser_on = 500 #ns
t_total = 2*(t_mw+t_buffer+t_laser_on+t_buffer)
print(t_total)

#patt0 = [(t_total,0)]
#patt1 = [(t_mw,0),(t_buffer,0),(t_laser_on,0),(t_buffer,0),(t_mw,1),(t_buffer,0),(t_laser_on,0),(t_buffer,0)]
#patt4 = [(t_mw,0),(t_buffer,0),(t_laser_on,1),(t_buffer,0),(t_mw,0),(t_buffer,0),(t_laser_on,1),(t_buffer,0)]

#patt1 = [(t_laser_on,0),(t_laser_on,0),(t_laser_on,0),(t_laser_on,0)]

aom_delay = 1073 #ns
aom_delay = 0
t_laser_on = 5000000 #ns
t_mw = 350 #ns
t_buffer = (100000-t_mw)/2
t_buffer1 = 140000#ns
t_buffer2 = 40000 #ns
t_buffer3 = 10000000-t_mw #ns

t_total=t_laser_on+t_buffer+t_mw+t_buffer+t_laser_on+t_buffer+t_mw+t_buffer+aom_delay
print(t_total)

patt0=[(aom_delay,0),(t_laser_on,0),(t_buffer1,0),(t_mw,0),(t_buffer2,0),(t_laser_on,0),(t_buffer,0),(t_mw,0),(t_buffer,0)]
patt1=[(aom_delay,0),(t_laser_on,0),(t_buffer1,0),(t_mw,1),(t_buffer2,0),(t_laser_on,0),(t_buffer,0),(t_mw,0),(t_buffer,0)]
patt3=[(aom_delay,0),(t_laser_on,1),(t_buffer1,0),(t_mw,0),(t_buffer2,0),(t_laser_on,0),(t_buffer,0),(t_mw,0),(t_buffer,0)]
patt4=[(t_laser_on,1),(t_buffer1,0),(t_mw,0),(t_buffer2,0),(t_laser_on,1),(t_buffer,0),(t_mw,0),(t_buffer,0),(aom_delay,0)]

patt0=[(aom_delay,0),(t_laser_on,0),(t_buffer1,0),(t_mw,0),(t_buffer2,0),(t_laser_on,0),(t_buffer3,0)]
patt1=[(aom_delay,0),(t_laser_on,0),(t_buffer1,0),(t_mw,1),(t_buffer2,0),(t_laser_on,0),(t_buffer3,0)]
patt3=[(aom_delay,0),(t_laser_on,1),(t_buffer1,0),(t_mw,0),(t_buffer2,0),(t_laser_on,0),(t_buffer3,0)]
patt4=[(t_laser_on,1),(t_buffer1,0),(t_mw,0),(t_buffer2,0),(t_laser_on,1),(t_buffer3,0),(aom_delay,0)]


seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(3, patt3) # TT trigger
seq.setDigital(4, patt4) # AOM
"""
########################################  T1 ###########################################################
"""
t_aom_delay = 1.073 #us
t_init=1000 #us 1000
t_readout_delay_max = 1000 #us
tau = 400
t_readout = 400 #us
t_wait = 2000 #us
num_samples = 10 # how many averages to perform at each tau in one iteration
clk_width = t_readout/2 #us, width of clk pulses--keep constant 

t_aom_delay = t_aom_delay*1e3
t_init = t_init*1e3
t_readout_delay_max = t_readout_delay_max*1e3
tau = tau*1e3
t_readout = t_readout*1e3
clk_width = clk_width*1e3


patt0 = [(t_aom_delay+t_init+tau+t_readout+t_readout_delay_max-tau+clk_width+t_wait,0)]

patt1 = [(t_aom_delay+t_init+tau+t_readout+t_readout_delay_max-tau+clk_width+t_wait,0)]

patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+tau+t_readout+t_readout_delay_max-tau-clk_width+clk_width+t_wait,0)]

patt3 = [(t_aom_delay+10,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-clk_width-t_readout-10+tau,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_readout_delay_max-tau+t_wait,0)]
#patt3 = [(t_aom_delay+t_init+tau,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_readout_delay_max-tau+t_wait,0)]

patt4 = [(t_init,1),(tau,0),(t_readout,1),(t_readout_delay_max-tau+clk_width+t_wait+t_aom_delay,0)]

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(2, patt2) # DAQ Trigger
seq.setDigital(3, patt3) # DAQ Clock
seq.setDigital(4, patt4) # AOM

"""
############################################# T1 TT###########################################################
"""
laser_power = 1#Vaom
global_delay = 0000#ns
aom_delay = 1073 #ns
aom_delay = 1073
t_laser_on = 30000000 #ns
t_readout_delay = 1000000 #ns
t_readout = 5000000 #ns
t_buffer = 20000000 - t_readout_delay#ns
bin_width = 20000#ns
print('Number of bins: ' + str((aom_delay+t_laser_on+t_readout_delay+t_readout+t_buffer)/bin_width))

patt0 =[(global_delay,0),(aom_delay,0),(t_laser_on,0),(t_readout_delay,0),(t_readout,0),(t_buffer,0)]
patt1 =[(global_delay,0),(aom_delay,0),(t_laser_on,0),(t_readout_delay-3000,0),(3000,0),(t_readout,0),(t_buffer,0)]
patt6 =[(aom_delay,0),(t_laser_on,1),(t_readout_delay,0),(t_readout,0),(t_buffer,0),(global_delay,0)]
patt5 =[(global_delay,1),(aom_delay,1),(t_laser_on,1),(t_readout_delay,1),(t_readout,1),(t_buffer,1)]
patt4 =[(global_delay,0),              (t_laser_on,1),(t_readout_delay,0),(t_readout,1),(t_buffer,0),(aom_delay,0)]
pattA1=[(global_delay,0),              (t_laser_on,laser_power),(t_readout_delay,0),(t_readout,laser_power),(t_buffer,0),(aom_delay,0)]

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(6, patt6) # TT trigger
seq.setDigital(5, patt5) # ZASWA SNSPD counts to TT
seq.setDigital(4, patt4) # AOM digital
seq.setAnalog(1, pattA1) # AOM analog
"""
######################################### Pulsed/transient EOM #########################################
"""
t_aom_delay = 1073
t_laser_on = 1000000
t_laser_off = 8000000
clk_width = t_laser_on/4


patt0 = [(t_aom_delay+t_laser_on+t_laser_off,0)] # rf switch EN

patt1 = [(t_aom_delay+t_laser_on+t_laser_off,0)] # rf switch CTRL

patt2 = [(t_aom_delay,0),(clk_width,1),(t_laser_on-clk_width,0),(t_laser_off,0)] # DAQ trigger

patt3 = [(t_aom_delay,0),(clk_width+10,1),(t_laser_on-clk_width-10,0),(clk_width,1),(t_laser_off-clk_width,0)] # DAQ binning division

patt4 = [(t_laser_on,1),(t_laser_off+t_aom_delay,0)] # aom digital in

pattA0 = [(t_laser_on,1.0),(t_laser_off+t_aom_delay,0.0)] # aom analog in, V

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(2, patt2) # TT trigger
seq.setDigital(3, patt3) # TT clk
seq.setDigital(4, patt4) # AOM
seq.setAnalog(1, pattA0) # AOM analog
"""
################################ Rabi with steady state init--affected by T1 ####################################
"""
t_aom_delay = 1.073 #us
t_start = 1000 #us
t_mw_delay = 73 #us
tau = 0.95 #us
tau_max = 2 #us
t_readout_delay = 4 #us
t_end = 1000 #us

t_aom_delay = t_aom_delay*1e3 #ns
t_start = t_start*1e3 #ns
t_mw_delay = t_mw_delay*1e3 #ns
tau = tau*1e3 #ns
tau_max = tau_max*1e3 #ns
t_readout_delay = t_readout_delay*1e3 #ns
t_end = t_end*1e3 #ns
clk_width = t_start/4 #ns

print((t_aom_delay+t_start+t_mw_delay+tau+t_readout_delay+t_end-tau+tau_max)/1e6)
print('ms')

patt0 = [(t_aom_delay+t_start+t_mw_delay+tau+t_readout_delay+t_end-tau+tau_max,0)]
patt1 = [(t_aom_delay+t_start+t_mw_delay,0),(tau,1),(t_readout_delay+t_end-tau+tau_max,0)]
patt3 = [(t_aom_delay,0),(clk_width,1),(t_start-clk_width+t_mw_delay+tau+t_readout_delay+t_end-tau+tau_max,0)]
patt4 = [(t_start,1),(t_mw_delay+tau+t_readout_delay,0),(t_end-tau+tau_max+t_aom_delay,1)]
pattA1 = [(t_start,1),(t_mw_delay+tau+t_readout_delay,0),(t_end-tau+tau_max+t_aom_delay,1)]

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(3, patt3) # TT clk
seq.setDigital(4, patt4) # AOM
seq.setAnalog(1, pattA1) # AOM analog
"""
################################ Rabi with steady state init--hopefully not affected by T1 #########################
"""
t_aom_delay = 1.073 #us
t_laser_on = 500 #us
t_laser_off = 28*3 #us
tau = 0.12 #us

t_aom_delay = t_aom_delay*1e3 #ns
t_laser_on = t_laser_on*1e3 #ns
t_laser_off = t_laser_off*1e3 #ns
tau = tau*1e3 #ns
clk_width = t_laser_on/4 #ns
t_buffer_2 = 100#ns
t_buffer_1 = (t_laser_off-tau-t_buffer_2) #ns


print((t_aom_delay+t_laser_on+t_laser_off+t_laser_on+t_laser_off)/1e6)
print('ms')

patt0 = [(t_aom_delay+t_laser_on+t_laser_off+t_laser_on+t_laser_off,0)]
patt1 = [(t_aom_delay+t_laser_on+t_buffer_1,0),(tau,1),(t_buffer_2+t_laser_on+t_laser_off,0)]
patt3 = [(t_aom_delay,0),(clk_width,1),(t_laser_on-clk_width+t_laser_off+t_laser_on+t_laser_off,0)]
patt4 = [(t_laser_on,1),(t_laser_off,0),(t_laser_on,1),(t_laser_off,0)]
pattA1 = [(t_laser_on,1),(t_laser_off,0),(t_laser_on,1),(t_laser_off,0)]

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(3, patt3) # TT clk
seq.setDigital(4, patt4) # AOM
seq.setAnalog(1, pattA1) # AOM analog
"""
################################ poor man's pODMR and wait time analysis ###########################################
"""
t_aom_delay = 1.073 #us
t_start = 1000 #us
t_mw_delay = 76 #us
tau = 0.4 #us
t_readout_delay = 4 #us
t_readout = 1000 #us
t_wait = 00*3 #us

t_aom_delay = t_aom_delay*1e3 #ns
t_start = t_start*1e3 #ns
t_mw_delay = t_mw_delay*1e3 #ns
tau = tau*1e3 #ns
t_readout_delay = t_readout_delay*1e3 #ns
t_readout = t_readout*1e3 #ns
t_wait = t_wait*1e3
clk_width = t_start/2 #ns

print((t_aom_delay+t_start+t_mw_delay+tau+t_readout_delay+t_readout+t_wait)/1e6)
print('ms')

patt0 = [(t_aom_delay+t_start+t_mw_delay+tau+t_readout_delay+t_readout+t_wait,0)]
patt1 = [(t_aom_delay+t_start+t_mw_delay,0),(tau,1),(t_readout_delay+t_readout+t_wait,0)]
patt3 = [(t_aom_delay,0),(clk_width,1),(t_start-clk_width+t_mw_delay+tau+t_readout_delay+t_readout+t_wait,0)]
patt4 = [(t_start,1),(t_mw_delay+tau+t_readout_delay,0),(t_readout,1),(t_wait+t_aom_delay,1)]
pattA1 = [(t_start,1),(t_mw_delay+tau+t_readout_delay,0),(t_readout,1),(t_wait+t_aom_delay,1)]

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(3, patt3) # TT clk
seq.setDigital(4, patt4) # AOM
seq.setAnalog(1, pattA1) # AOM analog
"""
################################ poor man's Ramsey ###########################################
"""
t_aom_delay = 1.073 #us
t_start = 5000 #us
t_mw_delay = 170 #us
t_pi = 0.850 #us
t_interpulse_delay = 0.1 #us
t_readout_delay = 40 #us
t_readout = 3000 #us
t_wait = 3500*3 #us

t_aom_delay = t_aom_delay*1e3 #ns
t_start = t_start*1e3 #ns
t_mw_delay = t_mw_delay*1e3 #ns
t_pi = t_pi*1e3 #ns
t_pi2 = t_pi/2 #ns
t_interpulse_delay = t_interpulse_delay*1e3 #ns
t_readout_delay = t_readout_delay*1e3 #ns
t_readout = t_readout*1e3 #ns
t_wait = t_wait*1e3
clk_width = t_start/2 #ns

print((t_aom_delay+t_start+t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay+t_readout+t_wait)/1e6)
print('ms')

patt0 = [(t_aom_delay+t_start+t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay+t_readout+t_wait,0)]
patt1 = [(t_aom_delay+t_start+t_mw_delay,0),(t_pi2,1),(t_interpulse_delay,1),(t_pi2,1),(t_readout_delay+t_readout+t_wait,0)]
patt3 = [(t_aom_delay,0),(clk_width,1),(t_start-clk_width+t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay+t_readout+t_wait,0)]
patt4 = [(t_start,1),(t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay,0),(t_readout,1),(t_wait+t_aom_delay,0)]
pattA1 = [(t_start,1),(t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay,0),(t_readout,1),(t_wait+t_aom_delay,0)]

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(3, patt3) # TT clk
seq.setDigital(4, patt4) # A91
seq.setAnalog(1, pattA1) # AOM analog
"""
################################ poor man's Ramsey a la nspyre ###########################################
"""
t_aom_delay = 1.073 #us
t_start = 5000 #us
t_mw_delay = 170 #us
t_pi = 0.850 #us
t_interpulse_delay = 0.1 #us
t_readout_delay = 40 #us
t_readout = 3000 #us

t_aom_delay = t_aom_delay*1e3 #ns
t_start = t_start*1e3 #ns
t_mw_delay = t_mw_delay*1e3 #ns
t_pi = t_pi*1e3 #ns
t_pi2 = t_pi/2 #ns
t_interpulse_delay = t_interpulse_delay*1e3 #ns
t_readout_delay = t_readout_delay*1e3 #ns
t_readout = t_readout*1e3 #ns
clk_width = t_readout/2 #ns

print((t_aom_delay+t_start+t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay+t_readout+clk_width+t_start+t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay+t_readout+clk_width)/1e6)
print('ms')

patt0 = [(t_aom_delay+t_start+t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay+t_readout+clk_width,0),
                     (t_start+t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay+t_readout+clk_width,0)]
patt1 = [(t_aom_delay+t_start+t_mw_delay,0),(t_pi2,1),(t_interpulse_delay,1),(t_pi2,1),(t_readout_delay+t_readout+clk_width,0),
                     (t_start+t_mw_delay,0),(t_pi2,0),(t_interpulse_delay,1),(t_pi2,0),(t_readout_delay+t_readout+clk_width,0)]
patt3 = [(t_aom_delay,0),(clk_width,1),(t_start-clk_width+t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay+t_readout+clk_width,0),
                     (t_start+t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay+t_readout+clk_width,0)]
patt4 = [(t_start,1),(t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay,0),(t_readout,1),(clk_width,0),
         (t_start,1),(t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay,0),(t_readout,1),(clk_width+t_aom_delay,0)]
pattA1 = [(t_start,1),(t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay,0),(t_readout,1),(clk_width,0),
          (t_start,1),(t_mw_delay+t_pi2+t_interpulse_delay+t_pi2+t_readout_delay,0),(t_readout,1),(clk_width+t_aom_delay,0)]

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(3, patt3) # TT clk
seq.setDigital(4, patt4) # A91
seq.setAnalog(1, pattA1) # AOM analog
"""
################################ poor man's pODMR a la nspyre ###########################################
"""
t_aom_delay = 1.073 #us
t_start = 500 #us
t_mw_delay = 75 #us
t_pi = 0.2 #us
t_readout_delay = 4 #us
t_readout = 1000 #us

t_aom_delay = t_aom_delay*1e3 #ns
t_start = t_start*1e3 #ns
t_mw_delay = t_mw_delay*1e3 #ns
t_pi = t_pi*1e3 #ns
t_pi2 = t_pi/2 #ns
t_readout_delay = t_readout_delay*1e3 #ns
t_readout = t_readout*1e3 #ns
clk_width = t_readout/2 #ns

print((t_aom_delay+t_start+t_mw_delay+t_pi+t_readout_delay+t_readout+clk_width+t_start+t_mw_delay+t_pi+t_readout_delay+t_readout+clk_width)/1e6)
print('ms')

patt0 = [(t_aom_delay+t_start+t_mw_delay+t_pi2+t_readout_delay+t_readout+clk_width,0),
                     (t_start+t_mw_delay+t_pi2+t_readout_delay+t_readout+clk_width,0)]
patt1 = [(t_aom_delay+t_start+t_mw_delay,0),(t_pi,1),(t_readout_delay+t_readout+clk_width,0),
                     (t_start+t_mw_delay,0),(t_pi,0),(t_readout_delay+t_readout+clk_width,0)]
patt3 = [(t_aom_delay,0),(clk_width,1),(t_start-clk_width+t_mw_delay+t_pi+t_readout_delay+t_readout+clk_width,0),
                     (t_start+t_mw_delay+t_pi+t_readout_delay+t_readout+clk_width,0)]
patt4 = [(t_start,1),(t_mw_delay+t_pi+t_readout_delay,0),(t_readout,1),(clk_width,1),
         (t_start,1),(t_mw_delay+t_pi+t_readout_delay,0),(t_readout,1),(clk_width+t_aom_delay,1)]
pattA1 = [(t_start,1),(t_mw_delay+t_pi+t_readout_delay,0),(t_readout,1),(clk_width,1),
          (t_start,1),(t_mw_delay+t_pi+t_readout_delay,0),(t_readout,1),(clk_width+t_aom_delay,1)]

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(3, patt3) # TT clk
seq.setDigital(4, patt4) # A91
seq.setAnalog(1, pattA1) # AOM analog
"""
################################ pODMR abbr ###########################################
"""
t_aom_delay = 1.073 #us
t_init = 1000 #us
t_mw_delay = 28*5 #us
t_rabi = 0.7 #us
t_readout_delay = 4 #us
t_readout = 300 #us
t_wait = 2000 #us

t_aom_delay = t_aom_delay*1e3 #ns
t_init = t_init*1e3 #ns
t_mw_delay = t_mw_delay*1e3 #ns
t_rabi = t_rabi*1e3 #ns
t_readout_delay = t_readout_delay*1e3 #ns
t_readout = t_readout*1e3 #ns
t_wait = t_wait*1e3 #ns
clk_width = t_readout/2 #ns

tau = t_rabi
t_rabi_max = 1000

print((t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay+t_init+t_wait)/1e6)
print('ms')

patt0 = [(t_aom_delay+t_init+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+clk_width+t_wait,0)]

patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(tau,1),(t_readout_delay+t_init+t_rabi_max-tau+clk_width+t_wait,0)]

patt2 = [(t_aom_delay,0),(clk_width,1),(t_init-clk_width+t_mw_delay+tau+t_readout_delay+t_init+t_rabi_max-tau+clk_width+t_wait,0)]

patt3 = [(t_aom_delay+100,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-t_readout-clk_width-100+t_mw_delay+tau+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init-t_readout-clk_width+t_rabi_max-tau+t_wait,0)]

patt4 = [(t_init,1),(t_mw_delay+tau+t_readout_delay,0),(t_init+t_rabi_max-tau+clk_width,1),(t_wait+t_aom_delay,0)]

pattA1= [(t_init,1.0),(t_mw_delay+tau+t_readout_delay,0.0),(t_init+t_rabi_max-tau+clk_width,1.0),(t_wait+t_aom_delay,0)]

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(2, patt2) # TT trigger
seq.setDigital(3, patt2) # TT clk
seq.setDigital(4, patt4) # AOM
seq.setAnalog(1, pattA1) # AOM analog
"""
###################################### test ############################################################
"""
t_aom_delay = 1.073 #us
t_init = 5000 #us
t_mw_delay = 5090 #us
t_mw =300 #us
t_readout_delay = 5390 #us
t_readout = 300 #us
t_wait = 900#us

t_aom_delay = t_aom_delay*1e3 #ns
t_init = t_init*1e3 #ns
t_mw_delay = t_mw_delay*1e3 #ns
t_mw = t_mw*1e3 #ns
t_readout_delay = t_readout_delay*1e3 #ns
t_readout = t_readout*1e3 #ns
t_wait = t_wait*1e3
clk_width = t_readout/2 #ns

# quasi podmr
patt0 = [(t_aom_delay+t_init+t_wait+clk_width,0),
                        (t_init+t_wait+clk_width,0)]

patt1 = [(t_aom_delay+t_mw_delay,0),(t_mw,1),(t_init+t_wait-t_mw_delay-t_mw+clk_width,0),
                        (t_mw_delay,0),(t_mw,0),(t_init+t_wait-t_mw_delay-t_mw+clk_width,0)]

patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+t_wait-clk_width+clk_width,0),
                            (clk_width,0),(t_init+t_wait-clk_width+clk_width,0)]

patt3 = [(t_aom_delay+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init+t_wait-t_readout_delay-t_readout,0),
                        (t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),(t_init+t_wait-t_readout_delay-t_readout,0)]

patt4 = [(t_init,1),(t_wait+clk_width,0),
            (t_init,1),(t_wait+clk_width+t_aom_delay,0)]

#t_wait > t_readout_delay-t_init+t_readout
patt4 = [(t_init,1),(t_readout_delay-t_init,1),(t_readout,1),(t_wait-(t_readout_delay-t_init)-t_readout+clk_width,0),
            (t_init,1),(t_readout_delay-t_init,1),(t_readout,1),(t_wait-(t_readout_delay-t_init)-t_readout+clk_width+t_aom_delay,0)]

pattA1 = [(t_init,1),(t_wait+clk_width,0),
            (t_init,1),(t_wait+clk_width+t_aom_delay,0)]

pattA1 = [(t_init,1),(t_readout_delay-t_init,0.5),(t_readout,1),(t_wait-(t_readout_delay-t_init)-t_readout+clk_width,0),
            (t_init,1),(t_readout_delay-t_init,0.5),(t_readout,1),(t_wait-(t_readout_delay-t_init)-t_readout+clk_width+t_aom_delay,0)]
"""
"""
t_aom_delay = 1.073 #us
t_init = 5000 #us
t_mw_delay = 90 #us
t_mw =300 #us
t_readout_delay = 1 #us
t_readout = 300 #us
t_wait = 900#us

t_aom_delay = t_aom_delay*1e3 #ns
t_init = t_init*1e3 #ns
t_mw_delay = t_mw_delay*1e3 #ns
t_mw = t_mw*1e3 #ns
t_readout_delay = t_readout_delay*1e3 #ns
t_readout = t_readout*1e3 #ns
t_wait = t_wait*1e3
clk_width = t_readout/2 #ns

t_rabi = t_mw
patt0 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout+clk_width,0),
                        (t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout+clk_width,0)]

patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(t_rabi,1),(t_readout_delay+t_readout+clk_width,0),
                        (t_init+t_mw_delay,0),(t_rabi,0),(t_readout_delay+t_readout+clk_width,0)]

patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout-clk_width+clk_width,0),
                            (clk_width,0),(t_init+t_mw_delay+t_rabi+t_readout_delay+t_readout-clk_width+clk_width,0)]

patt3 = [(t_aom_delay+t_init+t_mw_delay+t_rabi+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),
                        (t_init+t_mw_delay+t_rabi+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1)]

patt4 = [(t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,1),(clk_width,0),
            (t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,1),(clk_width+t_aom_delay,0)]

pattA1 = [(t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,1),(clk_width,0),
            (t_init,1),(t_mw_delay+t_rabi+t_readout_delay,0),(t_readout,1),(clk_width+t_aom_delay,0)]

"""
"""
t_aom_delay = 1.073 #us
t_init = 5000 #us
t_mw_delay = 90 #us
t_mw = 300 #us
t_readout_delay = 0.1 #us
t_readout = 300 #us
t_wait = 100#us
t_rabi = 300000#ns
t_rabi2 = t_rabi/2
t_interpulse_delay = 300#ns

t_aom_delay = t_aom_delay*1e3 #ns
t_init = t_init*1e3 #ns
t_mw_delay = t_mw_delay*1e3 #ns
t_mw = t_mw*1e3 #ns
t_readout_delay = t_readout_delay*1e3 #ns
t_readout = t_readout*1e3 #ns
t_wait = t_wait*1e3
clk_width = t_readout/2 #ns


patt0 = [(t_aom_delay+t_init+t_mw_delay+t_rabi2+t_interpulse_delay+t_rabi+t_interpulse_delay+t_rabi2+t_readout_delay+t_readout+clk_width,0),
                        (t_init+t_mw_delay+t_rabi2+t_interpulse_delay+t_rabi+t_interpulse_delay+t_rabi2+t_readout_delay+t_readout+clk_width,0)]

patt1 = [(t_aom_delay+t_init+t_mw_delay,0),(t_rabi2,1),(t_interpulse_delay,0),(t_rabi,1),(t_interpulse_delay,0),(t_rabi2,1),(t_readout_delay+t_readout+clk_width,0),
                        (t_init+t_mw_delay,0),(t_rabi2,0),(t_interpulse_delay,0),(t_rabi,0),(t_interpulse_delay,0),(t_rabi2,0),(t_readout_delay+t_readout+clk_width,0)]

patt2 = [(t_aom_delay,0),(clk_width,1),(t_init+t_mw_delay+t_rabi2+t_interpulse_delay+t_rabi+t_interpulse_delay+t_rabi2+t_readout_delay+t_readout-clk_width+clk_width,0),
                            (clk_width,0),(t_init+t_mw_delay+t_rabi2+t_interpulse_delay+t_rabi+t_interpulse_delay+t_rabi2+t_readout_delay+t_readout-clk_width+clk_width,0)]

patt3 = [(t_aom_delay+t_init+t_mw_delay+t_rabi2+t_interpulse_delay+t_rabi+t_interpulse_delay+t_rabi2+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1),
                        (t_init+t_mw_delay+t_rabi2+t_interpulse_delay+t_rabi+t_interpulse_delay+t_rabi2+t_readout_delay,0),(clk_width,1),(t_readout-clk_width,0),(clk_width,1)]

patt4 = [(t_init,1),(t_mw_delay+t_rabi2+t_interpulse_delay+t_rabi+t_interpulse_delay+t_rabi2+t_readout_delay,0),(t_readout,1),(clk_width,0),
            (t_init,1),(t_mw_delay+t_rabi2+t_interpulse_delay+t_rabi+t_interpulse_delay+t_rabi2+t_readout_delay,0),(t_readout,1),(clk_width+t_aom_delay,0)]

pattA1 = [(t_init,1),(t_mw_delay+t_rabi2+t_interpulse_delay+t_rabi+t_interpulse_delay+t_rabi2+t_readout_delay,0),(t_readout,1),(clk_width,0),
            (t_init,1),(t_mw_delay+t_rabi2+t_interpulse_delay+t_rabi+t_interpulse_delay+t_rabi2+t_readout_delay,0),(t_readout,1),(clk_width+t_aom_delay,0)]
seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(2, patt2) # TT trigger
seq.setDigital(3, patt3) # TT clk
seq.setDigital(4, patt4) # A91
seq.setAnalog(1, pattA1) # AOM analog
"""
####################################### cwODMR #########################################################
"""
laser_power = 1
dwell_rate = 2000 #Hz
duty_cycle = 1 #%
bin_width = 50000#ns

dwell_time = 1/dwell_rate*1e9 #ns
cooling_time = (100/duty_cycle)*dwell_time*(1-2*(duty_cycle/100)) #ns
clk_width = dwell_time/4 #ns

print('Num bins: '+ str((cooling_time+dwell_time+dwell_time)/bin_width))

patt0 = [(cooling_time+dwell_time+dwell_time,0),(cooling_time,0)]

patt1 = [(cooling_time+dwell_time,0),(498000,0),(dwell_time-498000,1),(cooling_time,0)]

patt2 = [(clk_width,1),(cooling_time-clk_width+dwell_time+dwell_time,0),(cooling_time,0)]

patt3 = [(clk_width,1),(cooling_time-clk_width,0),(clk_width,1),(dwell_time-clk_width,0),(clk_width,1),(dwell_time-clk_width,0),(cooling_time,0)]

patt4 = [(cooling_time,1),(dwell_time,1),(dwell_time,0),(10000000,1),(cooling_time-10000000,0)]

patt5 = [(cooling_time+dwell_time+dwell_time,1),(cooling_time,1)]

pattA1= [(cooling_time,laser_power),(dwell_time,laser_power),(dwell_time,0),(10000000,laser_power),(cooling_time-10000000,0)]

print((cooling_time+dwell_time+dwell_time)/1e9)

seq.setDigital(0, patt0) # switch EN
seq.setDigital(1, patt1) # switch CTRL
seq.setDigital(3, patt3) #to view clking
seq.setDigital(6, patt2) # TT trigger
seq.setDigital(5, patt5) # ZASWA SNSPD counts to TT
seq.setDigital(4, patt4) # AOM digital
seq.setAnalog(1, pattA1) # AOM analog
"""
########################################################################################################

seq.plot()

########################################################################################################

ps.stream(seq)