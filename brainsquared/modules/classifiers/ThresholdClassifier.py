import json
import logging
import time

from brainsquared.modules.classifiers.ClassifierModuleAbstract \
  import ClassifierModuleAbstract

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)



class ThresholdClassifier(ClassifierModuleAbstract):
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
    Classify with simple thresholds.
    
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

    super(ThresholdClassifier, self).__init__(user_id,
                                              device_type,
                                              rmq_address,
                                              rmq_user,
                                              rmq_pwd,
                                              input_metrics,
                                              output_metrics,
                                              module_id)

    # Set when configure() is called.
    self.thresholds = None
    self.input_metric_num_channels = None

    # Module specific
    self._last_classification = {
      "timestamp": int(time.time() * 1000),
      "channel_0": -1
      }  # -1 is "do nothing"


  def configure(self, thresholds):
    """
   Configure the module

    :param thresholds: If input value is over the threshold, 
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
                      
    :type thresholds: dict of floats
    """

    self.thresholds = thresholds

    # assume num_channels = num_thresholds
    self.input_metric_num_channels = len(thresholds)


  def start(self):
    self._process(self._classify)


  def _process(self, data_processor):
    """
    Subscribe to one input (1:1 mapping to routing key), process data, 
    and publish it back. 
    
    :param data_processor: function to process the data. 
    :type data_processor: Function that takes as input a list of dicts and 
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
      buffer_out = data_processor(buffer_in)  # output data buffered
      publisher.publish(routing_key_out, buffer_out)
      _LOGGER.debug(ch, method, properties, body)


    subscriber.subscribe(routing_key_in, callback)
    _LOGGER.info("[Module %s] Classifier module started.\n Routing keys: %s"
                 % (self.module_id, self.routing_keys))


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

      input_data = _convert_neurosky(input_data)

      activated_thresholds = {}
      active_channel = -1
      for i in range(self.input_metric_num_channels):
        channel_name = "channel_{}".format(i)
        if input_data[channel_name] > self.thresholds[channel_name]:
          activated_thresholds[i] = 1
          active_channel = i
        else:
          activated_thresholds[i] = 0

      sum_activated_thresholds = 0
      for t in activated_thresholds.values():
        sum_activated_thresholds += t

      _LOGGER.info("--> activated_thresholds: %s" % activated_thresholds)
      _LOGGER.info("--> SUM activated_thresholds: %s"
                   % sum_activated_thresholds)

      timestamp = input_data["timestamp"]
      # -1 means "do nothing". Any other index means the chanel with this index 
      # wins.
      if sum_activated_thresholds == 0:
        # Nothing to 1. So do nothing (i.e. class = neutral)
        # NOTE: by convention neutral is equal to num_channels. So if you 
        # have 2 channels (channel_0 and channel 1) then:
        # - Channel_0 wins => classification = 0 
        # - Channel_1 wins => classification = 1
        # - No channel win => classification = 2  (= num_channels) 
        classification = self.input_metric_num_channels  
      elif sum_activated_thresholds == 1:
        # Only one channel to 1
        classification = active_channel
      else:
        # More than 1 channel to 1. Hard to disambiguate. So remember the last 
        # class
        classification = self._last_classification["channel_0"]

      classification_result = {
        "timestamp": timestamp,
        "channel_0": classification
        }
      self._last_classification = classification_result

      _LOGGER.info(classification)

      buffer_out.append(classification_result)

    return buffer_out



def _convert_neurosky(input_data):
  """Trick to have neurosky data in the right cloudbrain format"""
  return {
    "timestamp": input_data["timestamp"],
    "channel_0": input_data["meditation"],
    "channel_1": input_data["attention"]
    }
