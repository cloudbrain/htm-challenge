import json
import logging
import os
import csv
import numpy as np

from sklearn import svm
from sklearn.externals import joblib

import brainsquared
from brainsquared.modules.classifiers.ClassifierModuleAbstract \
  import ClassifierModuleAbstract
from brainsquared.utils.metadata import get_num_channels

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

_DATA_DIR = "data"
_MODELS_DIR = "models"

if not os.path.exists(_MODELS_DIR):
  os.makedirs(_MODELS_DIR)
if not os.path.exists(_DATA_DIR):
  os.makedirs(_DATA_DIR)

CLASSIFIER_PATH = os.path.join(
  _MODELS_DIR, "%(classifier_type)s-%(device)s-%(input_metric)s.pkl")
VALID_CLASSIFIER_TYPES = ["svm"]

TRAINING_DATA_PATH = os.path.join(
  _DATA_DIR, "data-%(tag)s-%(device)s-%(metric)s.csv")



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
    self.classifier_type = None
    self.num_categories = None


  def configure(self, classifier_type, num_categories):
    """
   Configure the module

    :param classifier_type: type of sklearn classifier (e.g: "svm", "knn", ...)
    :type classifier_type: string
    """

    if classifier_type not in VALID_CLASSIFIER_TYPES:
      raise ValueError("Classifier type invalid (%s). Valid classifier types "
                       "are: %s" % (classifier_type, VALID_CLASSIFIER_TYPES))

    self.classifier_type =classifier_type
    self.classifier_path = CLASSIFIER_PATH % {
      "classifier_type": classifier_type,
      "device": self.device_type,
      "input_metric": self.input_metric
    }

    self.num_categories = num_categories


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
      classification = int(self.classifier.predict(to_classify)[0])
      classification_result = {
        "timestamp": timestamp,
        "channel_0": classification
      }
      _LOGGER.info("Classification: %s" % classification)
      buffer_out.append(classification_result)
    return buffer_out


  def train(self):
    categories = range(self.num_categories)
    num_channels = get_num_channels(self.device_type, self.input_metric)

    labels = []
    input_values = []
    for category in categories:
      input_file = TRAINING_DATA_PATH % {
        "tag": category,
        "metric": self.input_metric,
        "device": self.device_type
      }
      with open(input_file, "rb") as csvFile:
        reader = csv.reader(csvFile)
        headers = reader.next()

        for row in reader:
          data = dict(zip(headers, row))
          channel_values = []
          category = data["tag"]
          for i in range(num_channels):
            channel = "channel_%s" % i
            channel_values.append(float(data[channel]))
          input_values.append(channel_values)
          labels.append(category)

    num_records = len(input_values)
    num_train_records = num_records * 2 / 3
    train_input_values = input_values[:num_train_records]
    test_input_values = input_values[num_train_records:]
    train_labels = labels[:num_train_records]
    test_labels = labels[num_train_records:]

    X = np.array(train_input_values)
    y = np.array(train_labels)

    if self.classifier_type == "svm":
      clf = svm.LinearSVC()
    else:
      raise ValueError("Classifier type is '%s' but can only be: %s"
                       % VALID_CLASSIFIER_TYPES)

    clf.fit(X, y)

    X_test = np.array(test_input_values)
    y_test = np.array(test_labels)

    score = clf.score(X_test, y_test)

    classifier_path = CLASSIFIER_PATH % {
      "classifier_type": self.classifier_type,
      "device": self.device_type,
      "input_metric": self.input_metric
    }

    model_path = os.path.join(
      os.path.dirname(brainsquared.__file__), "module_runners",
      classifier_path)
    joblib.dump(clf, model_path)
    return classifier_path, score
