#!/usr/bin/env python2

# from eeg_preprocessing import preprocess_morlet, preprocess_stft
import matplotlib.pyplot as plt

metadata = {
    "left": {"main":"channel_0", "artifact":["channel_1", "channel_2", "channel_3"] },
    "right": {"main":"channel_4", "artifact":["channel_5", "channel_6", "channel_7" ] },
}

arrs, tag = preprocess_stft_file('../data/motor_data.csv', metadata)


plt.subplot(311)
plt.plot(arrs['left'])
plt.subplot(312)
plt.plot(arrs['right'])
plt.subplot(313)
plt.plot(tag)
plt.show()
