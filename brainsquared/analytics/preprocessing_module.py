import logging
import json

from brainsquared.publishers.PikaPublisher import PikaPublisher
from brainsquared.subscribers.PikaSubscriber import PikaSubscriber
from brainsquared.analytics.preprocessing.eeg_preprocessing import \
  preprocess_stft

_ROUTING_KEY = "%s:%s:%s"

# EEG electrodes placement
_METADATA = {
  "left": {
    "main": "channel_3", "unused": ["channel_0", "channel_4", "channel_6"]
    },
  "right": {
    "main": "channel_5", "unused": ["channel_2", "channel_4", "channel_7"]
    },
}

# metric names conventions
_EEG = "eeg"
_MU = "mu"

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)



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


  def initialize(self):
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


  def _preprocess(self, ch, method, properties, body):
    eeg = json.loads(body)
    timestamp = eeg[-1]["timestamp"]
    process = preprocess_stft(eeg, _METADATA)
    
    mu_left = process['left'][-1]
    mu_right = process['right'][-1]

    data = {"timestamp": timestamp, "left": mu_left, "right": mu_right} 
    
    _LOGGER.debug("--> mu: %s" % data)
    self.mu_publisher.publish(self.routing_keys[_MU], data)

