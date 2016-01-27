# #!/usr/bin/env python2

from cloudbrain.subscribers.PikaSubscriber import PikaSubscriber
from cloudbrain.settings import RABBITMQ_ADDRESS

import matplotlib.pyplot as plt
import numpy as np
import time
import json
import mne

from scipy import signal

device_id = "brainsquared"
device_name = "openbci"
metric = 'mu'

host = RABBITMQ_ADDRESS
buffer_size = 100

fig = plt.figure()
ax = fig.add_subplot(111)

N_points = 128
extra = 0

data = [0 for i in range(N_points)]
data2 = [0 for i in range(N_points)]
# data[0] = 0
# data[1] = 0


count = 0

b1, a1 = signal.iirfilter(1, [59.0/125.0, 61.0/125.0], btype='bandstop')
b2, a2 = signal.iirfilter(1, 3.0/125.0, btype='highpass')

# some X and Y data
x = np.arange(N_points)
y = data

# lis = [None] * 8

li, = ax.plot(x, y)
li2, = ax.plot(x, y)

# draw and show it
fig.canvas.draw()
plt.show(block=False)

def update_plot():
    global data, data2, b, a

    # plt.clf()
    # set the new data
    data_f = data
    # data_f = signal.lfilter(b1, a1, data_f)
    # data_f = signal.lfilter(b2, a2, data_f)
    data_f = data_f[-N_points:]
    # data_f = data
    li.set_ydata(data)
    li2.set_ydata(data2)

    ax.relim()
    ax.autoscale_view(True,True,True)
    fig.canvas.draw()


    # plt.clf()
    # spec = plt.specgram(data_f, NFFT=128, noverlap=32, Fs=250, detrend='mean', pad_to=256,
    #                     scale_by_freq=True)

    # # X = mne.time_frequency.stft(data, wsize)
    # # freqs = mne.time_frequency.stftfreq(wsize, sfreq=fs)

    # # imshow(np.log(abs(X[0])), aspect='auto',
    # #        origin='lower', interpolation="None",
    # #        vmin=-14, vmax=-4,
    # #        extent=[0, 4, 0, max(freqs)])
    # # ylim([0, 60])

    plt.draw()
    # # draw()


    # time.sleep(0.001)
    plt.pause(0.0001)                       #add this it will be OK.


def consume_eeg(connection,deliver,properties,msg_s):
    global data, data2, count

    # print(msg_s)
    
    msg = json.loads(msg_s)
    d = []
    # for row in msg[-32:]:
    #     # print(row)
    #     d.append(float(row['channel_0']))

    print(msg['left'], msg['right'])
    # print(len(msg))

    data.append(msg['left'])
    data2.append(msg['right'])

    data = data[-N_points-extra:]
    data2 = data2[-N_points-extra:]
    
    update_plot()

eeg_subscriber = PikaSubscriber(device_name, device_id, host, metric)
eeg_subscriber.connect()

eeg_subscriber.consume_messages(consume_eeg)

# # loop to update the data
# while True:
#     try:
#         try:
#             x = float(s.readline().strip())
#         except ValueError:
#             continue

#         data.append(x)
#         data = data[-100:]

#         # set the new data
#         li.set_ydata(data)

#         ax.relim()
#         ax.autoscale_view(True,True,True)
#         fig.canvas.draw()

#         # time.sleep(0.001)
#         plt.pause(0.0001)                       #add this it will be OK.
#     except KeyboardInterrupt:
#         break
