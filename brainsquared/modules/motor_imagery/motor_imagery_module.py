import logging
import time
import csv

#import simplejson
import json
import numpy as np


from htmresearch.frameworks.classification.utils.network_config import \
  generateNetworkPartitions

from brainsquared.publishers.PikaPublisher import PikaPublisher
from brainsquared.subscribers.PikaSubscriber import PikaSubscriber

from brainsquared.modules.motor_imagery.htm_classifier import HTMClassifier


with open("data/min_max.csv", "rb") as f:
  reader = csv.reader(f)
  reader.next()
  reader.next()
  reader.next()
  _MU_MIN = float(reader.next()[1])
  _MU_MAX = float(reader.next()[1])

_LEARNING_IS_ON = True
_NETWORK_CONFIG = "config/network_config.json"
_TRAINING_DATA = "data/min_max.csv"
_TRAIN_SET_SIZE = 2000
_PRE_TRAIN = False
_ROUTING_KEY = "%s:%s:%s"

_N_CONFIG = {
  "sensorRegionConfig": {
    "regionEnabled": True,
    "regionName": "sensor",
    "regionType": "py.CustomRecordSensor",
    "regionParams": {
      "verbosity": 1,
      "numCategories": 3
    },
    "encoders": {
      "scalarEncoder": {
        "name": "scalarEncoder",
        "fieldname": "y",
        "type": "ScalarEncoder",
        "n": 256,
        "w": 21,
        "minval": None,
        "maxval": None
      }
    }
  },
  "spRegionConfig": {
    "regionEnabled": True,
    "regionName": "SP",
    "regionType": "py.SPRegion",
    "regionParams": {
      "spVerbosity": 0,
      "spatialImp": "cpp",
      "globalInhibition": 1,
      "columnCount": 2048,
      "numActiveColumnsPerInhArea": 40,
      "seed": 1956,
      "potentialPct": 0.8,
      "synPermConnected": 0.1,
      "synPermActiveInc": 0.0001,
      "synPermInactiveDec": 0.0005,
      "maxBoost": 1.0
    }
  },
  "tmRegionConfig": {
    "regionEnabled": True,
    "regionName": "TM",
    "regionType": "py.TPRegion",
    "regionParams": {
      "verbosity": 0,
      "columnCount": 2048,
      "cellsPerColumn": 32,
      "seed": 1960,
      "temporalImp": "tm_py",
      "newSynapseCount": 20,
      "maxSynapsesPerSegment": 32,
      "maxSegmentsPerCell": 128,
      "initialPerm": 0.21,
      "permanenceInc": 0.1,
      "permanenceDec": 0.1,
      "globalDecay": 0.0,
      "maxAge": 0,
      "minThreshold": 9,
      "activationThreshold": 12,
      "outputType": "normal",
      "pamLength": 3
    }
  },
  "tpRegionConfig": {
    "regionEnabled": False,
    "regionName": "TP",
    "regionType": "py.TemporalPoolerRegion",
    "regionParams": {
      "poolerType": "union",
      "columnCount": 512,
      "activeOverlapWeight": 1.0,
      "predictedActiveOverlapWeight": 10.0,
      "maxUnionActivity": 0.20,
      "synPermPredActiveInc": 0.1,
      "synPermPreviousPredActiveInc": 0.1,
      "decayFunctionType": "NoDecay"
    }
  },
  "classifierRegionConfig": {
    "regionEnabled": True,
    "regionName": "classifier",
    "regionType": "py.CLAClassifierRegion",
    "regionParams": {
      "steps": "0",
      "implementation": "cpp",
      "maxCategoryCount": 3,
      "clVerbosity": 0
    }
  }
}


logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


#with open(_NETWORK_CONFIG, "rb") as jsonFile:
#  network_config = simplejson.load(jsonFile)
network_config = _N_CONFIG # TODO: temp fix for offline work
partitions = generateNetworkPartitions(network_config, _TRAIN_SET_SIZE)



class HTMMotorImageryModule(object):
  
  def __init__(self,
               user_id,
               module_id,
               device_type,
               rmq_address,
               rmq_user,
               rmq_pwd):

    self.stats =  {"min": None, "max": None}

    self.module_id = module_id
    self.user_id = user_id
    self.device_type = device_type
    self.rmq_address = rmq_address
    self.rmq_user = rmq_user
    self.rmq_pwd = rmq_pwd
    
    # These have to be set with configure()
    self.input_metric = None
    self.output_metric = None
    self.tag_metric = None
    self.categories = None
    
    self.last_tag = None
    
    self.output_metric_publisher = None
    self.input_metric_subscriber = None
    self.tag_subscriber = None
    self.tag_publisher = None

    self.routing_keys = None
    self.start_time = int(time.time() * 1000)  # in ms

    self.classifier = None
    self.numRecords = 0
    self.learning_mode = True


  def configure(self, input_metric, tag_metric, output_metric, categories):
    self.input_metric = input_metric
    self.output_metric = output_metric
    self.tag_metric = tag_metric
    self.categories = categories
    

  def connect(self):
    """
    Initialize classifier, publisher (classification), and subscribers (mu 
    and tag)
    """
    
    if self.input_metric is None:
      raise ValueError("Input metric can't be none. "
                       "Use configure() to set it.")
    if self.output_metric is None:
      raise ValueError("Output metric can't be none. "
                       "Use configure() to set it.")
    if self.tag_metric is None:
      raise ValueError("Tag metric can't be none. "
                       "Use configure() to set it.")
    if self.categories is None:
      raise ValueError("Categories can't be none. "
                       "Use configure() to set it.")
    
    # Init tag with first category
    self.last_tag = {"timestamp": self.start_time, "value": self.categories[0]}
      
    self.routing_keys = {
      self.input_metric: _ROUTING_KEY % (self.user_id, self.device_type,
                                         self.input_metric),
      self.output_metric: _ROUTING_KEY % (self.user_id, self.device_type,
                                          self.output_metric),
      self.tag_metric: _ROUTING_KEY % (self.user_id, self.device_type,
                                          self.tag_metric),
    }

    self.classifier = HTMClassifier(network_config, _TRAINING_DATA,
                                            self.categories)
    self.classifier.connect()
    if _PRE_TRAIN:
      self.classifier.train(_TRAIN_SET_SIZE, partitions)


    self.tag_subscriber = PikaSubscriber(self.rmq_address,
                                         self.rmq_user, self.rmq_pwd)
    self.tag_publisher = PikaPublisher(self.rmq_address,
                                         self.rmq_user, self.rmq_pwd)
    self.input_metric_subscriber = PikaSubscriber(self.rmq_address,
                                                  self.rmq_user, self.rmq_pwd)
    self.output_metric_publisher = PikaPublisher(self.rmq_address,
                                                 self.rmq_user, self.rmq_pwd)

    self.tag_subscriber.connect()
    self.tag_publisher.connect()
    self.input_metric_subscriber.connect()
    self.output_metric_publisher.connect()

    self.tag_subscriber.subscribe(self.routing_keys[self.tag_metric])
    self.tag_publisher.register(self.routing_keys[self.tag_metric])
    self.input_metric_subscriber.subscribe(self.routing_keys[self.input_metric])
    self.output_metric_publisher.register(self.routing_keys[self.output_metric])
    

  def start(self):
    
    _LOGGER.info("[Module %s] Starting Motor Imagery module. Routing keys: %s" 
                % (self.module_id, self.routing_keys))

   
    self.input_metric_subscriber.consume_messages(self.routing_keys["mu"],
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
    
    self.numRecords += 1
    print self.numRecords
    if self.numRecords > 1000:
      self.learning_mode = False
      print "=======LEARNING DISABLED!!!========="
      
    self.last_tag = self._update_last_tag(self.last_tag)
    _LOGGER.debug("[Module %s] mu: %s | last_tag: %s" % (self.module_id, body, 
                                                      self.last_tag))

    mu = json.loads(body)
    mu_timestamp = mu["timestamp"]
    tag_timestamp = self.last_tag["timestamp"]

    results = {}
    for (hemisphere, classifier) in self.classifier.items():
      mu_value = mu[hemisphere]
      tag_value = self.last_tag["value"]
      mu_clipped = np.clip(mu_value, _MU_MIN, _MU_MAX)
      
      results[hemisphere] = classifier.classify(input_data=mu_clipped,
                                                target=tag_value,
                                                learning_is_on=self.learning_mode)

      self._update_stats(hemisphere, mu_value)
      #_LOGGER.debug(self.stats)

    _LOGGER.debug("Raw results: %s" % results)      
     
    #classification_result = _reconcile_results(results['left'],
    #                                           results['right'])
    #TODO: make this cleaner
    classification_result = results['left']
    
    buffer = [{"timestamp": mu_timestamp, "value": classification_result}]

    self.output_metric_publisher.publish(self.routing_keys["classification"],
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
