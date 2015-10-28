import numpy as np

from nupic.encoders.base import Encoder
from nupic.encoders.scalar import ScalarEncoder



class EEGEncoder(Encoder):
  """
  This is an implementation of an EEG encoder. A frequency value is 
  extracted from an EEG wave and is encoded into an SDR using a ScalarEncoder.
  """


  def __init__(self, n, w, rate, chunk, minval, maxval, minFreq, maxFreq, 
               name=None):
    """
    @param n int the length of the encoded SDR
    @param w int the number of 1s in the encoded SDR
    @param rate int the number of EEG samples per second
    @param chunk int the number of samples in an input
    @param minval float the minval of the encoder
    @param maxval float the maxval of the encoder
    @param minFreq float the lowest possible frequency detected
    @param maxFreq float the highest possible frequency detected
    @param name string the name of the encoder
    """
    self.n = n
    self.w = w
    self.rate = rate
    self.chunk  = chunk
    self.minFreq = minFreq
    self.maxFreq = maxFreq
    self.name = name
    self._scalarEncoder = ScalarEncoder(name="scalar_"+str(name), n=n, w=w,
                                        minval=minval, maxval=maxval)


  def _getFrequencyAmplitude(self, inputArr):
    """
    Use FFT to find maximum frequency present in the input.
    @param inputArr (list of floats): chunk of data to take the FFT of.
    """
    
    #TODO: maybe take the log or convert to dB instead of just the FFT
    fftData=abs(np.fft.rfft(inputArr)) # absolute value to get real numbers
    freqs = np.fft.rfftfreq(len(inputArr), 1.0/self.rate)
    
    # Take the mean of the frequency amplitudes that are in the range of the 
    # min and max frequency. 
    amps = fftData[np.logical_and(freqs <= self.maxFreq, freqs >= self.minFreq)]
    return np.mean(amps)


  def encodeIntoArray(self, inputArr, output):
    if not isinstance(inputArr, (list, np.ndarray)):
      raise TypeError(
          "Expected a list or numpy array but got input of type %s" % type(inputArr))
    frequencyAmplitude = self._getFrequencyAmplitude(inputArr)
    output[0:self.n] = self._scalarEncoder.encode(frequencyAmplitude)


  def getWidth(self):
    return self.n
