#!/usr/bin/env python2

"""
This is a suite of functions useful for processing EEG data
all of the functions take a matrix X : [n_times, n_signals] of raw EEG data.
"""

import numpy as np
from scipy import stats

## for the morlet wavelet transform
import mne

## for the ICA, useful for removing eye blinks
from sklearn.decomposition import FastICA


def stft(X, y=None, box_width=256, step=32, pad_width=0, kaiser_beta=14, include_phase=False, log_mag=False):
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
        if end >= len(X):
            break

        x = X[start:end,]

        if pad_width > 0:
            x = np.vstack([x, np.zeros((pad_width, x.shape[1]))])

        x = (x.T * w).T

        fft = np.fft.rfft(x, axis=0)
        psd = np.abs(fft)
        if log_mag:
            psd = np.log(psd)
        
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
            h.append(np.log(np.abs(cwt[i].T)))
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
    ica = estimate_ica(X)
    ix = get_eye_blinks_ix(X, ica)
    return remove_eyeblinks(X, ica, ix)



## possible left/right configuration
## per Steve's idea
# left = (X[:, 0] - 0.33 * (X[:, 1] + X[:, 2] + X[:, 3]))
# right = (X[:, 4] - 0.33 * (X[:, 5] + X[:, 6] + X[:, 7]))

