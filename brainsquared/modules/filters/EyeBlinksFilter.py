import logging
import json
import numpy as np
import uuid

from brainsquared.utils.metadata import get_num_channels
from brainsquared.publishers.PikaPublisher import PikaPublisher
from brainsquared.subscribers.PikaSubscriber import PikaSubscriber
from brainsquared.modules.filters.eeg_preprocessing import (
  preprocess_stft, get_raw, EyeBlinksFilter, from_raw)

from threading import Thread

_ROUTING_KEY = "%s:%s:%s"

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)



class PreprocessingModule(object):
  def __init__(self,
               user_id,
               device_type,
               rmq_address,
               rmq_user,
               rmq_pwd,
               input_metrics,
               output_metrics):

    self.module_id = str(uuid.uuid4())
    
    self.user_id = user_id
    self.device_type = device_type
    self.rmq_address = rmq_address
    self.rmq_user = rmq_user
    self.rmq_pwd = rmq_pwd
    self.input_metrics = None
    self.output_metrics = None

    self.eeg_subscriber = None
    self.mu_publisher = None
    self.routing_keys = None
    self.preprocessor = None

    self.num_channels = get_num_channels(self.device_type, "eeg")
    self.eeg_data = np.zeros((0, self.num_channels))
    self.count = 0

    self.eyeblinks_remover = EyeBlinksFilter()

    self.step_size = None
    self.electrodes_placement = None
    self.enable_ica = False
    
    self.started_fit = False



  def configure(self, step_size, electrodes_placement, enable_ica=False):
    """
    Module specific params.
    @param step_size: (int) STFT step size
    @param electrodes_placement: (dict) dict with the electrode placement 
      for optional Laplacian filtering. 
      
      E.g:
      {
        "channel_2": {
           "main": "channel_2", 
           "artifact": ["channel_0", "channel_3", "channel_5"]
        },
        "channel_4": {
           "main": "channel_4", 
           "artifact": ["channel_1", "channel_3", "channel_6"]
        },
      }
      
      If you don't want any Laplacian filtering then set this to:
      {
        "channel_2": {
           "main": "channel_2", 
           "artifact": []
        },
        "channel_4": {
           "main": "channel_4", 
           "artifact": []
        },
      }
      
      More about Laplacian filtering: http://sccn.ucsd.edu/wiki/Flt_laplace  
    @param input_metric: (string) name of the input metric.
    @param output_metric: (string) name of the output metric.
    @param enable_ica: (boolean) if 1, enable ICA pre-processing. This will 
      remove eye blinks. 
    """
    self.step_size = step_size
    self.electrodes_placement = electrodes_placement
    self.input_metric = input_metric
    self.output_metric = output_metric
    self.enable_ica = enable_ica


  def connect(self):
    """
    Initialize EEG preprocessor, publisher, and subscriber
    """

    if self.step_size is None:
      raise ValueError("Step size can't be none. "
                       "Use configure() to set it.")
    if self.electrodes_placement is None:
      raise ValueError("Electrode placement can't be none. "
                       "Use configure() to set it.")
    if self.input_metric is None:
      raise ValueError("Input metric can't be none. "
                       "Use configure() to set it.")
    if self.output_metric is None:
      raise ValueError("Output metric can't be none. "
                       "Use configure() to set it.")

    self.routing_keys = {
      self.input_metric: _ROUTING_KEY % (self.user_id, self.device_type,
                                         self.input_metric),
      self.output_metric: _ROUTING_KEY % (self.user_id, self.device_type,
                                          self.output_metric)
    }

    self.mu_publisher = PikaPublisher(self.rmq_address,
                                      self.rmq_user, self.rmq_pwd)
    self.eeg_subscriber = PikaSubscriber(self.rmq_address,
                                         self.rmq_user, self.rmq_pwd)

    self.eeg_subscriber.connect()
    self.mu_publisher.connect()

    self.mu_publisher.register(self.routing_keys[self.output_metric])
    self.eeg_subscriber.register(self.routing_keys[self.input_metric])


  def start(self):
    _LOGGER.info("[Module %s] Starting Preprocessing. Routing "
                 "keys: %s" % (self.module_id, self.routing_keys))

    self.eeg_subscriber.subscribe(self.routing_keys[self.input_metric],
                                  self._preprocess)


  def refit_ica(self):
    t = Thread(target=self.eyeblinks_remover.fit, args=(self.eeg_data,))
    t.start()


  def _preprocess(self, ch, method, properties, body):
    eeg = json.loads(body)

    self.eeg_data = np.vstack([self.eeg_data, get_raw(eeg, self.num_channels)])

    self.count += self.step_size

    timestamp = eeg[-1]["timestamp"]

    if self.enable_ica:
      eeg = from_raw(self.eyeblinks_remover.transform(
          get_raw(eeg, self.num_channels)), self.num_channels)
      if ((self.count >= 5000 and not self.started_fit)
          or self.count % 10000 == 0):
        _LOGGER.info('refitting...')
        self.started_fit = True
        self.refit_ica()

    processed_data = preprocess_stft(eeg, self.electrodes_placement)

    data = {"timestamp": timestamp}
    for key, value in processed_data.items():
      data[key] = processed_data[key][-1]

    _LOGGER.debug("--> output: %s" % data)
    self.mu_publisher.publish(self.routing_keys[self.output_metric], data)
