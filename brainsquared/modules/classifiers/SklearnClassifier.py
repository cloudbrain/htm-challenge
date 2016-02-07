import json
import logging
import os

from sklearn.externals import joblib

import brainsquared
from brainsquared.modules.classifiers.ClassifierModuleAbstract \
  import ClassifierModuleAbstract
from brainsquared.utils.metadata import get_num_channels

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

_MODELS_DIR = "models"

if not os.path.exists(_MODELS_DIR):
  os.makedirs(_MODELS_DIR)

CLASSIFIER_PATH = os.path.join(
    _MODELS_DIR, "%(classifier_type)s-%(input_metric)s.pkl")
VALID_CLASSIFIER_TYPES = ["svm"]



class SKLearnClassifier(ClassifierModuleAbstract):
  def __init__(self,
               user_id,
               device_type,
               rmq_address,
               rmq_user,
               rmq_pwd,
               input_metrics,
               output_metrics,
               module_id=None):

    """
    :param user_id: ID of the user using the device.
    :type user_id: string
    
    :param device_type: type of the device publishing to this module. 
    :type device_type: string
    
    :param rmq_address: address of the RabbitMQ server.
    :type rmq_address: string
        
    :param rmq_user: login for RabbitMQ connection.
    :type rmq_user: string
    
    :param rmq_pwd: password for RabbitMQ connection.
    :type rmq_pwd: string
        
    :param input_metrics: name of the input metric.
    :type input_metrics: dict
    
    :param output_metrics: name of the output metric.
    :type output_metrics: dict
    
    :param module_id: (Optional. Default = None) ID of the module
    :type module_id: string
    """

    super(SKLearnClassifier, self).__init__(user_id,
                                            device_type,
                                            rmq_address,
                                            rmq_user,
                                            rmq_pwd,
                                            input_metrics,
                                            output_metrics,
                                            module_id)

    self.num_input_channels = get_num_channels(device_type, self.input_metric)

    # Set when configure() is called.
    self.classifier_path = None
    self.classifier = None


  def configure(self, classifier_type):
    """
   Configure the module

    :param classifier_type: type of sklearn classifier (e.g: "svm", "knn", ...)
    :type classifier_type: string
    """

    if classifier_type not in VALID_CLASSIFIER_TYPES:
      raise ValueError("Classifier type invalid (%s). Valid classifier types "
                       "are: %s" % (classifier_type, VALID_CLASSIFIER_TYPES))

    self.classifier_path = CLASSIFIER_PATH % {
      "classifier_type": classifier_type,
      "input_metric": self.input_metric
    }


  def start(self):
    self._load_classifier()
    self._process(self._classify)


  def _process(self, classify):
    """
    Subscribe to one input (1:1 mapping to routing key), process data, 
    and publish it back. 
    
    :param classify: function to classify the data. 
    :type classify: Function that takes as input a list of dicts and 
      outputs a list of dicts. Input/output list of dicts must have the 
      following 
      format:  
       {"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>}
    """
    publisher = self.publishers[self.output_metric_key]
    subscriber = self.subscribers[self.input_metric_key]
    # NOTE: we actually don't need tags in this module
    # tag_subscriber = self.subscribers[self.tag_metric_key]

    routing_key_out = self.routing_keys[self.output_metric_key]
    routing_key_in = self.routing_keys[self.input_metric_key]


    def callback(ch, method, properties, body):
      """Callback function called by the subscriber. Processes the data and 
      publishes it back"""
      buffer_in = json.loads(body)  # input data buffered
      buffer_out = classify(buffer_in)  # output data buffered
      publisher.publish(routing_key_out, buffer_out)
      _LOGGER.debug(ch, method, properties, body)


    subscriber.subscribe(routing_key_in, callback)
    _LOGGER.info("[Module %s] Classifier module started.\n Routing keys: %s"
                 % (self.module_id, self.routing_keys))


  def _load_classifier(self):

    model_path = os.path.join(os.path.dirname(brainsquared.__file__),
                              "module_runners", self.classifier_path)
    self.classifier = joblib.load(model_path)


  def _classify(self, buffer_in):
    """
    Classification logic.
    @param buffer_in: (list) buffer of input data to classify:
      [
       {
       "timestamp": <int>,
       "channel_0": <float>, 
       "channel_1": <float>, 
       },
       ...
       {
       "timestamp": <int>,
       "channel_0": <float>, 
       "channel_1": <float>, 
       }
       ]
    @return buffer_out: (dict) classification result: 
      [
       {
        "timestamp": <int>,
        "channel_0: <float>}
       },
       ...
       {
        "timestamp": <int>,
        "channel_0: <float>}
       }
      ]
    """

    buffer_out = []
    for input_data in buffer_in:
      timestamp = input_data["timestamp"]
      to_classify = [input_data["channel_%s" % i] for i in
                     range(self.num_input_channels)]
      classification = self.classifier.predict(to_classify)[0]
      classification_result = {
        "timestamp": timestamp,
        "channel_0": classification
      }
      _LOGGER.info("Classification: %s" % classification)
      buffer_out.append(classification_result)
    return buffer_out
