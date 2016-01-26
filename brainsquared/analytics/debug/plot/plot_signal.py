# #!/usr/bin/env python2

from cloudbrain.subscribers.PikaSubscriber import PikaSubscriber

import matplotlib.pyplot as plt
import numpy as np
import json

from scipy import signal

device_id = "brainsquared"
device_name = "openbci"
metric = 'eeg'

host = "localhost"
buffer_size = 100

fig = plt.figure()
ax = fig.add_subplot(111)

N_points = 1024
extra = 512

data = [0 for i in range(N_points)]
data2 = [0 for i in range(N_points)]

count = 0

b1, a1 = signal.iirfilter(1, [59.0/125.0, 61.0/125.0], btype='bandstop')
b2, a2 = signal.iirfilter(1, 3.0/125.0, btype='highpass')

# some X and Y data
x = np.arange(N_points)
y = data

li, = ax.plot(x, y)

# draw and show it
fig.canvas.draw()
plt.show(block=False)

def update_plot():
    global data, b, a

    # plt.clf()
    # set the new data
    data_f = data
    data_f = signal.lfilter(b1, a1, data_f)
    data_f = signal.lfilter(b2, a2, data_f)
    data_f = data_f[-N_points:]
    li.set_ydata(data_f)

    ax.relim()
    ax.autoscale_view(True,True,True)
    fig.canvas.draw()
    plt.draw()
    plt.pause(0.0001)       


def consume_eeg(connection,deliver,properties,msg_s):
    global data, count
    
    msg = json.loads(msg_s)
    d = []
    for row in msg[-32:]:
        d.append(float(row['channel_5']) - float(row['channel_3']))
      
    data.extend(d)
    data = data[-N_points-extra:]

    if count == 1:
        update_plot()
        count = 0
    else:
        count += 1

eeg_subscriber = PikaSubscriber(device_name, device_id, host, metric)
eeg_subscriber.connect()

eeg_subscriber.consume_messages(consume_eeg)
