import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from brainsquared.encoder.eeg_encoder import EEGEncoder


CHUNK = 128
SLIDING_WINDOW = 64
RATE = 250
MI_DATA = "data/motor_data.csv"


def visualizeSDRs(sdrs):
  sdrsToVisualize = []

  for sdr in sdrs:
    sdrsToVisualize.append([255 if x else 0 for x in sdr])

  imageArray = np.rot90(np.array(sdrsToVisualize))
  plt.imshow(imageArray, cmap='Greys',  interpolation='nearest')
  plt.show()


def recordAndEncode(encoder):

  window = np.blackman(CHUNK)
  sdrs = []

  print "---recording---"
  d = pd.read_csv(MI_DATA)
  data = np.array(d['channel_0'])  
  data = data[np.logical_not(np.isnan(data))]   
    
  for i in xrange(500, len(data)-CHUNK, SLIDING_WINDOW):
    chunk = data[i:i+CHUNK] * window
    sdr = encoder.encode(chunk)
    sdrs.append(sdr)

  print "---done---"
  return sdrs


if __name__ == "__main__":
  n = 300
  w = 31
  minFreq = 9
  maxFreq = 11
  minval = 0
  maxval = 0.005

  soundEncoder = EEGEncoder(n, w, RATE, CHUNK, minval, maxval, minFreq, maxFreq)
  sdrs = recordAndEncode(soundEncoder)
  visualizeSDRs(sdrs)


