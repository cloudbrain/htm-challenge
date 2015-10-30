#!/usr/bin/env python2

import numpy as np
import pandas as pd
from preprocess_eeg import wavelet_transform, remove_eyeblinks_full

import csv

in_fname = '../data/motor_data.csv'
out_fname = '../data/mu_motor_data.csv'

# ignore first n values, while EEG adjusts to baseline
ignore_first = 1100

data = pd.read_csv(in_fname)
vals = data.values
vals = vals[np.sum(np.isnan(vals), axis=1) == 0] # remove missing data
vals = vals[ignore_first:, :] # ignore first values
# tag = vals[:, -1]

X = remove_eyeblinks_full(vals)

cwt = wavelet_transform(X[:, :1], sfreq=250, freqs=[10], n_cycles=50, include_phase=True, log_mag=False)

tag = vals[:, -1]

f_writer = open(out_fname, 'w')
writer = csv.writer(f_writer)

writer.writerow(['x', 'y', 'label'])
writer.writerow(['float', 'float', 'int'])
writer.writerow(['', '', 'C'])

for i in xrange(cwt.shape[0]):
    mag, phase = cwt[i]
    row = [phase, mag, int(tag[i])] 
    writer.writerow(row)

f_writer.close()
