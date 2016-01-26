import logging
import json

import numpy as np

from brainsquared.publishers.PikaPublisher import PikaPublisher
from brainsquared.subscribers.PikaSubscriber import PikaSubscriber
from brainsquared.analytics.preprocessing.eeg_preprocessing import \
  preprocess_stft, get_raw, EyeBlinksRemover, from_raw

from threading import Thread

_ROUTING_KEY = "%s:%s:%s"

# EEG electrodes placement
_METADATA = {
  "right": {
    "main": "channel_2", "artifact": ["channel_0", "channel_3", "channel_5"]
    },
  "left": {
    "main": "channel_4", "artifact": ["channel_1", "channel_3", "channel_6"]
    },
}



# metric names conventions
_EEG = "eeg"
_MU = "mu"

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)



class PreprocessingModule(object):
  def __init__(self,
               user_id,
               module_id,
               device_type,
               rmq_address,
               rmq_user,
               rmq_pwd):
    self.user_id = user_id
    self.module_id = module_id
    self.device_type = device_type
    self.rmq_address = rmq_address
    self.rmq_user = rmq_user
    self.rmq_pwd = rmq_pwd

    self.eeg_subscriber = None
    self.mu_publisher = None

    self.routing_keys = {
      _EEG: _ROUTING_KEY % (user_id, device_type, _EEG),
      _MU: _ROUTING_KEY % (user_id, device_type, _MU)
    }

    self.preprocessor = None

    self.eeg_data = np.zeros((0,8))
    self.count = 0

    self.eyeblinks_remover = EyeBlinksRemover()

    self.step_size = 32

    self.started_fit = False
    
  def configure(self, step_size):
    """
    Module specific params.
    @param step_size: (int) STFT step size
    """
    self.step_size = step_size
    

  def connect(self):
    """
    Initialize EEG preprocessor, publisher, and subscriber
    """
    self.mu_publisher = PikaPublisher(self.rmq_address,
                                      self.rmq_user, self.rmq_pwd)
    self.eeg_subscriber = PikaSubscriber(self.rmq_address,
                                         self.rmq_user, self.rmq_pwd)

    self.eeg_subscriber.connect()
    self.mu_publisher.connect()

    self.mu_publisher.register(self.routing_keys[_MU])
    self.eeg_subscriber.subscribe(self.routing_keys[_EEG])


  def start(self):
    _LOGGER.info("[Module %s] Starting Preprocessing. Routing "
                 "keys: %s" % (self.module_id, self.routing_keys))

    self.eeg_subscriber.consume_messages(self.routing_keys[_EEG],
                                         self._preprocess)


  def refit_ica(self):
    t = Thread(target=self.eyeblinks_remover.fit, args=(self.eeg_data,))
    t.start()
    # self.eyeblinks_remover.fit(self.eeg_data[1000:])

  def _preprocess(self, ch, method, properties, body):
    eeg = json.loads(body)

    self.eeg_data = np.vstack([self.eeg_data, get_raw(eeg)])

    # self.count += len(eeg)
    self.count += self.step_size
    
    if (self.count >= 5000 and not self.started_fit) or self.count % 10000 == 0:
      _LOGGER.info('refitting...')
      self.started_fit = True
      self.refit_ica()


    timestamp = eeg[-1]["timestamp"]
    
    eeg = from_raw(self.eyeblinks_remover.transform(get_raw(eeg)))
    
    process = preprocess_stft(eeg, _METADATA)

    mu_left = process['left'][-1]
    mu_right = process['right'][-1]

    data = {"timestamp": timestamp, "left": mu_left, "right": mu_right}

    _LOGGER.debug("--> mu: %s" % data)
    self.mu_publisher.publish(self.routing_keys[_MU], data)


