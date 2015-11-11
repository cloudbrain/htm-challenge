import simplejson as json
import logging
import time
import numpy as np

from htmresearch.frameworks.classification.utils.network_config import \
  generateNetworkPartitions

from brainsquared.publishers.PikaPublisher import PikaPublisher
from brainsquared.subscribers.PikaSubscriber import PikaSubscriber

from brainsquared.analytics.motor_imagery.htm_classifier import HTMClassifier

_LEARNING_IS_ON = True
_NETWORK_CONFIG = "config/network_config.json"
_TRAINING_DATA = "data/training_data.csv"
_TRAIN_SET_SIZE = 2000
_PRE_TRAIN = False
_ROUTING_KEY = "%s:%s:%s"

# metric names conventions
_MU = "mu"
_MU_MIN = -6
_MU_MAX = 1
_TAG = "tag"
_CLASSIFICATION = "classification"

_CATEGORIES = ["baseline", "left", "right"]

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


with open(_NETWORK_CONFIG, "rb") as jsonFile:
  network_config = json.load(jsonFile)
partitions = generateNetworkPartitions(network_config, _TRAIN_SET_SIZE)



class HTMMotorImageryModule(object):
  def __init__(self,
               user_id,
               module_id,
               device_type,
               rmq_address,
               rmq_user,
               rmq_pwd):

    self.stats = {
      "left": {"min": None, "max": None},
      "right": {"min": None, "max": None}
      }
    self.module_id = module_id
    self.user_id = user_id
    self.device_type = device_type
    self.rmq_address = rmq_address
    self.rmq_user = rmq_user
    self.rmq_pwd = rmq_pwd
    
    self.classification_publisher = None
    self.mu_subscriber = None
    self.tag_subscriber = None
    self.tag_publisher = None

    self.routing_keys = {
      "mu": _ROUTING_KEY % (user_id, device_type, _MU),
      "tag": _ROUTING_KEY % (user_id, module_id, _TAG),
      "classification": _ROUTING_KEY % (user_id, module_id, _CLASSIFICATION)
    }

    self.start_time = int(time.time() * 1000)  # in ms
    self.last_tag = {"timestamp": self.start_time, "value": _CATEGORIES[1]}

    self.classifiers = {"left": None, "right": None}

  def initialize(self):
    """
    Initialize classifier, publisher (classification), and subscribers (mu 
    and tag)
    """

    self.classifiers["left"] = HTMClassifier(network_config, _TRAINING_DATA,
                                             _CATEGORIES)
    self.classifiers["right"] = HTMClassifier(network_config, _TRAINING_DATA,
                                              _CATEGORIES)
    for classifier in self.classifiers.values():
      classifier.initialize()
      if _PRE_TRAIN:
        classifier.train(_TRAIN_SET_SIZE, partitions)


    self.tag_subscriber = PikaSubscriber(self.rmq_address,
                                         self.rmq_user, self.rmq_pwd)
    self.tag_publisher = PikaPublisher(self.rmq_address,
                                         self.rmq_user, self.rmq_pwd)
    self.mu_subscriber = PikaSubscriber(self.rmq_address,
                                        self.rmq_user, self.rmq_pwd)
    self.classification_publisher = PikaPublisher(self.rmq_address,
                                                  self.rmq_user, self.rmq_pwd)

    self.tag_subscriber.connect()
    self.tag_publisher.connect()
    self.mu_subscriber.connect()
    self.classification_publisher.connect()

    self.tag_subscriber.subscribe(self.routing_keys["tag"])
    self.tag_publisher.register(self.routing_keys["tag"])
    self.mu_subscriber.subscribe(self.routing_keys["mu"])
    self.classification_publisher.register(self.routing_keys["classification"])
    

  def start(self):
    
    _LOGGER.info("[Module %s] Starting Motor Imagery module. Routing keys: %s" 
                % (self.module_id, self.routing_keys))

   
    self.mu_subscriber.consume_messages(self.routing_keys["mu"], 
                                        self._tag_and_classify)


  def _update_last_tag(self, last_tag):
    """Consume all tags in the queue and keep the last one (i.e. the most up 
    to date)"""
    while 1:
      (meth_frame, header_frame, body) = self.tag_subscriber.get_one_message(
        self.routing_keys["tag"])
      if body:
        last_tag = json.loads(body)
      else:
        return last_tag
  
  
  def _tag_and_classify(self, ch, method, properties, body):
    """Tag data and runs it through the classifier"""
    
    self.last_tag = self._update_last_tag(self.last_tag)
    _LOGGER.debug("[Module %s] mu: %s | last_tag: %s" % (self.module_id, body, 
                                                      self.last_tag))

    mu = json.loads(body)
    mu_timestamp = mu["timestamp"]
    tag_timestamp = self.last_tag["timestamp"]

    # skip classification if tag and mu have more than 1s delay
    skip_classification = False
    #if abs(tag_timestamp * 1000 - mu_timestamp) > 1000000: # in micro seconds
    #  skip_classification = True

    if not skip_classification:
      results = {}
      for (hemisphere, classifier) in self.classifiers.items():
        mu_value = mu[hemisphere]
        if mu_value > 0:
          pass

        tag_value = self.last_tag["value"]
        mu_clipped = np.clip(mu_value, _MU_MIN, _MU_MAX)
        results[hemisphere] = classifier.classify(input_data=mu_clipped,
                                                  target=tag_value,
                                                  learning_is_on=True)

        self._update_stats(hemisphere, mu_value)
        #_LOGGER.debug(self.stats)
      

      
      left_result = _CATEGORIES[int(results["left"])]
      right_result = _CATEGORIES[int(results["right"])]
      _LOGGER.debug("Raw results: %s" % results)      
      _LOGGER.debug("Human readable results: %s" % 
                    {"left_electrode_class": left_result,
                     "right_electrode_class": right_result})
       
      classification_result = _reconcile_results(left_result,
                                                 right_result)
      
      buffer = [{"timestamp": mu_timestamp, "value": classification_result}]

      self.classification_publisher.publish(self.routing_keys["classification"],
                                            buffer)


  def _update_stats(self, hemisphere, mu_value):
    """
    Update stats.
     self.stats = {
      "left": {"min": None, "max": None},
      "right": {"min": None, "max": None}
      }
    """
    min_val = self.stats[hemisphere]["min"]
    max_val = self.stats[hemisphere]["max"]
    
    if not min_val:
      self.stats[hemisphere]["min"] = mu_value
    if not max_val:
      self.stats[hemisphere]["max"] = mu_value  
    if mu_value < min_val:
      self.stats[hemisphere]["min"] = mu_value
    if mu_value > max_val:
      self.stats[hemisphere]["max"] = mu_value  


def _reconcile_results(left_result, right_result):
  """
  Reconcile results from the left and right electrodes and their respective 
  models.
  @param left_result: result from the left electrode classification
  @param right_result: result from the right electrode classification
  @return: result after reconciliation of the two input results.
  """


  if left_result == "left" and right_result == "left":
    return -2
  elif left_result == "right" and left_result == "right":
    return 2
  elif left_result == "left" and right_result == "left":
    return -1
  elif left_result == "right" and right_result == "right":
    return 1
  else:
    return 0
      
