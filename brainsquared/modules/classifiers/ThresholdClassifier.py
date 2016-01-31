import logging
import json
import time 

from brainsquared.publishers.PikaPublisher import PikaPublisher
from brainsquared.subscribers.PikaSubscriber import PikaSubscriber

_ROUTING_KEY = "%s:%s:%s"

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)



class ThresholdClassifier(object):
  def __init__(self,
               user_id,
               device_type,
               rmq_address,
               rmq_user,
               rmq_pwd,
               input_metrics,
               output_metrics):

    """
    Classify with simple thresholds. 
    
    Metrics conventions:
    - Data to classify: {"timestamp": <int>, "channel_0": <float>}
    - Data label: {"timestamp": <int>, "channel_0": <int>}
    - Classification result: {"timestamp": <int>, "channel_0": <int>}
    
    @param user_id: (string) ID of the user using the device. 
    @param device_type: (string) type of the device publishing to this module. 
    @param rmq_address: (string) address of the RabbitMQ server.
    @param rmq_user: (string) login for RabbitMQ connection.
    @param rmq_pwd: (string) password for RabbitMQ connection.
    @param input_metrics: (list) name of the input metric.
    @param output_metrics (list)  name of the output metric.
    """

    self.module_id = ThresholdClassifier.__name__

    self.user_id = user_id
    self.device_type = device_type
    self.rmq_address = rmq_address
    self.rmq_user = rmq_user
    self.rmq_pwd = rmq_pwd
    self.input_metrics = input_metrics
    self.output_metrics = output_metrics

    self.input_metric = None
    self.output_metric = None
    self.tag_metric = None
    self.last_tag = {"timestamp": None, "channel_0": None}

    self.output_metric_publisher = None
    self.input_metric_subscriber = None
    self.tag_subscriber = None
    self.routing_keys = None

    # Set when configure() is called.
    self.thresholds = None
    self.input_metric_num_channels = None
    
    # Module specific
    self._last_classification = {"timestamp": int(time.time() * 1000), 
                                 "channel_0": -1}  # -1 is "do nothing"


  def _validate_metrics(self):
    """
    Validate input and output metrics and initialize them accordingly.
    
    This module must have the following signature for input and output metrics:
    
    input_metrics = {"metric_to_classify": <string>, "label_metric": <string>}
    output_metrics = {"result_metric": <string>}
    """

    if "label_metric" in self.input_metrics:
      self.tag_metric = self.input_metrics["label_metric"]
    else:
      raise KeyError("The input metric 'label_metric' is not set!")

    if "metric_to_classify" in self.input_metrics:
      self.input_metric = self.input_metrics["metric_to_classify"]
    else:
      raise KeyError("The input metric 'metric_to_classify' is not set!")

    if "result_metric" in self.output_metrics:
      self.output_metric = self.output_metrics["result_metric"]
    else:
      raise KeyError("The output metric 'result_metric' is not set!")


  def configure(self, thresholds):
    """
   Configure the module

    @param thresholds: (dict of float) If input value is over the threshold, 
      then publish 1. Otherwise, publish 0. This dict must have the 
      same number of keys as the input metrics. E.g:
        input_metric = {timestamp: <int>, 
                        channel_0: <float>, 
                        ...
                        channel_N: <float>}
    
        thresholds = {timestamp: <int>, 
                      channel_0: <float>, 
                       ...
                      channel_N: <float>}
    
    
    @param thresholds: (dict of floats) If value is over a threshold, 
      then return 1. Otherwise, return 0. 
    """

    self._validate_metrics()
    self.thresholds = thresholds

    # assume num_channels = num_thresholds
    self.input_metric_num_channels = len(thresholds)


  def connect(self):
    """
    Initialize EEG preprocessor, publisher, and subscriber
    """

    if self.input_metric is None:
      raise ValueError("Input metric can't be none. "
                       "Use configure() to set it.")
    if self.output_metric is None:
      raise ValueError("Output metric can't be none. "
                       "Use configure() to set it.")

    self.routing_keys = {
      self.input_metric: _ROUTING_KEY % (self.user_id, self.device_type,
                                         self.input_metric),
      self.output_metric: _ROUTING_KEY % (self.user_id, self.module_id,
                                          self.output_metric)
    }

    self.output_metric_publisher = PikaPublisher(self.rmq_address,
                                                 self.rmq_user, self.rmq_pwd)
    self.input_metric_subscriber = PikaSubscriber(self.rmq_address,
                                                  self.rmq_user, self.rmq_pwd)

    self.input_metric_subscriber.connect()
    self.output_metric_publisher.connect()

    self.output_metric_publisher.register(self.routing_keys[self.output_metric])
    self.input_metric_subscriber.subscribe(self.routing_keys[self.input_metric])


  def start(self):
    _LOGGER.info("[Module %s] Starting Preprocessing. Routing "
                 "keys: %s" % (self.module_id, self.routing_keys))

    self.input_metric_subscriber.consume_messages(
        self.routing_keys[self.input_metric], self._process)


  def _process(self, ch, method, properties, body):

    input_buffer = json.loads(body)
    output_buffer = []
    for input_data in input_buffer:
      output_data = self._classify(input_data, self.thresholds)
      output_buffer.append(output_data)

    _LOGGER.debug("--> output: %s" % output_buffer)
    self.output_metric_publisher.publish(self.routing_keys[self.output_metric],
                                         output_buffer)


  def _classify(self, input_data, thresholds):
    """
    Classification logic.
    @param input_data: (dict)input data to classify:
      {
       "timestamp": <int>,
       "channel_0": <float>, 
       "channel_1": <float>, 
       }
    @param thresholds: (dict of floats) If value is over a threshold, 
      then return 1. Otherwise, return 0. 
    @return output_data: (dict) classification result: 
      {
       "timestamp": <int>,
       "channel_0: <float>}
      }
    """

 
    activated_thresholds = {}
    for i in range(self.input_metric_num_channels):
      channel_name = "channel_{}".format(i)
      if input_data[channel_name] > thresholds[channel_name]:
        activated_thresholds[i] = 1
      else:
        activated_thresholds[i] = 0

    _LOGGER.info("--> activated_thresholds: %s" % activated_thresholds)
    _LOGGER.info("--> SUM activated_thresholds: %s" 
                  % sum(activated_thresholds))
    
    timestamp = input_data["timestamp"]
    # -1 means "do nothing". Any other index means the chanel with this index 
    # wins.
    if sum(activated_thresholds.values()) == 0:
      # Nothing to 1. So do nothing.
      classification = -1
    elif sum(activated_thresholds.values()) == 1:
      # Only one channel to 1
      classification = [i for i, value in enumerate(activated_thresholds) 
                        if value != 0][0]
    else:
      # More than 1 channel to 1. Hard to disambiguate. So remember the last 
      # class
      classification = self._last_classification["channel_0"]

    classification_result = {"timestamp": timestamp, 
                             "channel_0": classification}      
    self._last_classification = classification_result
    
    
    _LOGGER.info(classification)

    return classification_result

    # concentration_threshold = thresholds["channel_0"]
    # meditation_threshold = thresholds["channel_1"]
    # 
    # if input_data["channel_0"] > concentration_threshold:
    #   attention = True
    # else:
    #   attention = False
    # 
    # if input_data["channel_1"] > meditation_threshold:
    #   meditation = True
    # else:
    #   meditation = False
    # 
    # if meditation and not attention:
    #   classification = -1
    # elif attention and not meditation:
    #   classification = 1
    # else:
    #   classification = self.last_classification
    # 
    # self.last_class = classification
    # 
    # output_data = {
    #   "timestamp": timestamp,
    #   "channel_0": classification
    # }
    # 
    # return output_data
