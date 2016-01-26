#!/usr/bin/env python2

## this is a suite of functions useful for processing EEG data
## all of the functions take a matrix X : [n_times, n_signals] of raw EEG data

import numpy as np
from scipy import stats
from scipy import signal

## for the morlet wavelet transform
import mne

## for the ICA, useful for removing eye blinks
from sklearn.decomposition import FastICA

import pandas as pd
import csv
import os.path

def stft(X, y=None, box_width=128, step=32, pad_width=0, kaiser_beta=14, include_phase=True, log_mag=False):
    """performs short time fourier transform, with Kaiser window

    Parameters
    ----------
    X : array of shape [n_times, n_signals]
        raw EEG data
    y : array of shape [n_times]
        tags of data (optional, could be None)
        useful to keep track of which tags belong to what
    box_width: int
        length of FFT window
    step: int
        how many samples should we advance the window by
    pad_width: int
        number of samples to pad the fourier transform width
    kaiser_beta: float
        positive number indicating beta parameter for the Kaiser window
        increasing beta decreases aliasing, but also decreases frequency resolution
        see https://en.wikipedia.org/wiki/Kaiser_window
    include_phase: bool
        if False, only returns magnitude of decomposition components
        if True, also returns the angle of the components
    log_mag: bool
        whether or not to take the log of the magnitude
    Returns
    -------
    out: 2D array
        Time Frequency Decomposition of signal
        rows are time, columns are features
        columns are magnitude of different frequencies and,
          if include_phase is True, phases of the component at each frequency
    """

    out_X = []
    out_y = []
    m = int(X.shape[0] / box_width) * box_width

    w = np.kaiser(box_width + pad_width, kaiser_beta)

    for start in range(0, m, step):
        end = start + box_width
        if end > len(X):
            break

        x = X[start:end,]

        if pad_width > 0:
            x = np.vstack([x, np.zeros((pad_width, x.shape[1]))])

        x = (x.T * w).T

        fft = np.fft.rfft(x, axis=0)
        psd = np.abs(fft)
        if log_mag:
            psd = np.log(psd+1)

        #freqs, psd = signal.welch(X[start:end,], axis=0)
        row = psd.flatten()

        if include_phase:
            angle = np.angle(fft)
            row = np.append(row, angle.flatten())

        out_X.append(row)

        if y is not None:
            out_y.append(stats.mode(y[start:end])[0][0])

    if y is not None:
        return np.array(out_X), np.array(out_y)
    else:
        return np.array(out_X)

def wavelet_transform(X, sfreq=250, freqs=np.arange(8,12, 0.5), n_cycles=50, include_phase=True, log_mag=False):
    """performs continuous wavelet transform, using complex morlet wavelet
    uses mne.time_frequency.tfr.cwt_morlet

    Parameters
    ----------
    X : array of shape [n_times, n_signals]
        raw EEG data
    sfreq : float
        sampling frequency
    freqs : array
        Array of frequencies of interest
    n_cycles: float | array of float
        Number of cycles. Fixed number or one per frequency.
        Higher number gives better frequency resolution, lower temporal resolution
        (basically smooths out the signal in time).
    include_phase: bool
        if False, only returns magnitude of decomposition components
        if True, also returns the angle of the components
    log_mag: bool
        whether or not to take the log of the magnitude
    Returns
    -------
    out: 2D array
        Time Frequency Decompositions (n_times x (n_signals x n_frequencies))
        Column number may be (n_signals x n_frequencies x 2) if include_phase = True
    """
    cwt = mne.time_frequency.tfr.cwt_morlet(X.T, sfreq=sfreq, freqs=freqs,
                                            n_cycles=n_cycles,
                                            zero_mean=True, use_fft=True)

    h = []

    for i in range(cwt.shape[0]):
        if log_mag:
            h.append(np.log(np.abs(cwt[i].T)+1))
        else:
            h.append(np.abs(cwt[i].T))

    if include_phase:
        for i in range(cwt.shape[0]):
            h.append(np.angle(cwt[i].T))

    out = np.hstack(h)

    return out



def estimate_ica(X):
    ica = FastICA(n_components=X.shape[1])
    ica.fit(X)
    return ica

def get_eye_blinks_ix(X, ica):
    sources = ica.transform(X)
    return np.argmax(stats.kurtosis(sources))


def remove_eyeblinks(X, ica, eye_blinks_ix):
    means = ica.mean_.copy()
    mixing = ica.mixing_.copy()
    mixing[:, eye_blinks_ix] = 0

    sources = ica.transform(X)
    out = sources.dot(mixing.T) + means

    return out


class EyeBlinksRemover(object):
    def __init__(self):
        self._ica = None
        self._eyeblinks_ix = None
        self.fitted = False

    def fit(self, X):
        self._ica = estimate_ica(X)
        self._eyeblinks_ix = get_eye_blinks_ix(X, self._ica)
        self.fitted = True
        return self

    def transform(self, X):
        if self.fitted:
            return remove_eyeblinks(X, self._ica, self._eyeblinks_ix)
        else:
            return X # failsafe

    def fit_transform(self, X):
        return self.fit(X).transform(X)



## this is a separate function
## because in real time, it's better to do something like:
## - get some data (maybe 10-20 seconds worth?) with eyeblinks
## - estimate ICA and find eye blinks component
## - store ICA and eye blinks component
## - call remove_eyeblinks on streaming data

## note that this is fully unsupervised
## we can re-estimate the ICA as new data streams in
## it's pretty fast
def remove_eyeblinks_full(X):
    return EyeBlinksRemover().fit_transform(X)



## possible left/right configuration
## per Steve's idea
# left = (X[:, 0] - 0.33 * (X[:, 1] + X[:, 2] + X[:, 3]))
# right = (X[:, 4] - 0.33 * (X[:, 5] + X[:, 6] + X[:, 7]))

## data:
## [{'timestamp': 10, 'channel_0': 0.59, ...},
# {'timestamp': 10, 'channel_0': 0.59, ...},
# {'timestamp': 10, 'channel_0': 0.59, ...},
# ...
# ]

# metadata: <dict>
# {
# "left": {"main":"channel_3", "artifact":["channel_0", "channel_4", "channel_6"] },
# "right": {"main":"channel_5", "artifact":["channel_2", "channel_4", "channel_7" ] },
# }


def get_raw_arrs(data, metadata):
    out = dict()

    for k in metadata.keys():
        out[k] = np.zeros(len(data))

    for i, row in enumerate(data):
        for k, meta in metadata.items():
            val = float(row[meta['main']])
            artifacts = meta.get('artifact', [])
            for c in artifacts:
                a = float(row[c])
                val -= a / float(len(artifacts))

            out[k][i] = val

    return out


def get_raw(data):
    """
    Transform rabbitMQ format to matrix.
    Assuming data is a series of dict() objects with
    'channel_0' through 'channel_7' as keys
    
    @param data: 
    @return: 
    """
    channels = ['channel_{}'.format(i) for i in range(8)]
    out = np.zeros((len(data),8))
    for i, row in enumerate(data):
        arr = [row[c] for c in channels]
        out[i, :] = np.array(arr)
    return out

def from_raw(data):
    channels = ['channel_{}'.format(i) for i in range(8)]
    out = []
    for i in xrange(data.shape[0]):
        out.append(dict(zip(channels, data[i,:])))
    return out
# downsampling_factor: <float> (default value = 32)

## output
# {'left': preprocessed_mu,  'right': preprocessed_mu}
## downsampling factor must be int

## takes in a function f
## f : array of raw data -> preprocessed array
def preprocess_general(process, data, metadata):
    raw_arrs = get_raw_arrs(data, metadata)

    arrs = dict()

    for name, arr in raw_arrs.items():
        arrs[name] = process(arr)

    return arrs


def preprocess_morlet(data, metadata, notch_filter=True, downsampling_factor=32,
                      sfreq=250, freqs=[10], n_cycles=50):

    b1, a1 = signal.iirfilter(1, [59.0/125.0, 61.0/125.0], btype='bandstop')
    b2, a2 = signal.iirfilter(1, 3.0/125.0, btype='highpass')

    def do_morlet(arr):

        if notch_filter:
            arr = signal.lfilter(b1, a1, arr)
            arr = signal.lfilter(b2, a2, arr)

        cwt = wavelet_transform(arr[:, np.newaxis], sfreq=sfreq, freqs=freqs,
                                n_cycles=n_cycles, include_phase=False,
                                log_mag=True)

        arr = cwt.mean(axis=1)

        if downsampling_factor > 1:
            decimated = signal.decimate(arr, downsampling_factor)
        else:
            decimated = arr

        return decimated

    return preprocess_general(process=do_morlet,
                              data=data, metadata=metadata)


def preprocess_stft(data, metadata, notch_filter=True,
                    box_width=128, downsampling_factor=32,
                    sfreq=250, low_f=8, high_f=12, kaiser_beta=14):

    b1, a1 = signal.iirfilter(1, [59.0/125.0, 61.0/125.0], btype='bandstop')
    b2, a2 = signal.iirfilter(1, 3.0/125.0, btype='highpass')

    def do_stft(arr):

        if notch_filter:
            arr = signal.lfilter(b1, a1, arr)
            arr = signal.lfilter(b2, a2, arr)
            if len(arr) < box_width:
                raise ValueError("The buffer_size used by the connector should "
                                 "be higher than box_width. buffer_size = "
                                 "%s | box_width = %s" % (len(arr), box_width))

        out = stft(arr[:, np.newaxis],
                   box_width=box_width, step=downsampling_factor, pad_width=0,
                   kaiser_beta=kaiser_beta, include_phase=False, log_mag=True)

        fftfreq = np.fft.rfftfreq(box_width, d=1/float(sfreq))
        good = np.logical_and(fftfreq >= low_f, fftfreq <= high_f)
        out = out[:, good].mean(axis=1)

        return out



    return preprocess_general(process=do_stft,
                              data=data, metadata=metadata)




def write_arrs_to_files(out_dir, arrs, tagd):
    fnames = dict()

    for name, processed in arrs.items():
        out_fname = os.path.join(out_dir, '{}_test.csv'.format(name))

        f_writer = open(out_fname, 'w')
        writer = csv.writer(f_writer)

        writer.writerow(['x', 'y', 'label'])
        writer.writerow(['float', 'float', 'int'])
        writer.writerow(['', '', 'C'])

        for i in xrange(processed.shape[0]):
            # mag, phase = cwt[i]
            mag = processed[i]
            row = [i, mag, tagd[i]]
            writer.writerow(row)

        f_writer.close()

        fnames[name] = out_fname

    return fnames



def read_file_to_buffer(path_to_csv):
    f = open(path_to_csv, 'r')
    reader = csv.DictReader(f)

    out = []

    for row in reader:
        r = dict()
        for k, v in row.items():
            if v == None or v == 'nan':
                r = False
                break
            try:
                r[k] = float(v)
            except ValueError:
                r[k] = v
        if r:
            out.append(r)

    return out

def preprocess_stft_file(path_to_csv, metadata,
                    box_width=128, downsampling_factor=32,
                    sfreq=250, low_f=8, high_f=12, kaiser_beta=14,
                    ignore_first=1000, remove_eyeblinks=True):

    data = read_file_to_buffer(path_to_csv)
    data = data[ignore_first:]
    tag = np.array([row['tag'] for row in data])

    if remove_eyeblinks:
        data = from_raw(remove_eyeblinks_full(get_raw(data)))

    arrs = preprocess_stft(data, metadata,
                    box_width=box_width, downsampling_factor=downsampling_factor,
                    sfreq=sfreq, low_f=low_f, high_f=high_f, kaiser_beta=kaiser_beta)

    N = arrs.values()[0].shape[0]
    tagd = tag[::downsampling_factor][:N]

    return arrs, tagd

def preprocess_morlet_file(path_to_csv, metadata,
                           box_width=128, downsampling_factor=32,
                           sfreq=250, freqs=[10], n_cycles=50,
                           ignore_first=1000, remove_eyeblinks=True):

    data = read_file_to_buffer(path_to_csv)
    data = data[ignore_first:]
    tag = np.array([row['tag'] for row in data])

    if remove_eyeblinks:
        data = from_raw(remove_eyeblinks_full(get_raw(data)))
    
    arrs = preprocess_morlet(data, metadata,
                             box_width=box_width, downsampling_factor=downsampling_factor,
                             sfreq=sfreq, freqs=freqs, n_cycles=n_cycles)

    N = arrs.values()[0].shape[0]
    tagd = tag[::downsampling_factor][:N]

    return arrs, tagd
