import logging
import time
import simplejson
import numpy as np

from nupic.engine import Network
from nupic.data.file_record_stream import FileRecordStream

from htmresearch.frameworks.classification.classification_network import (
  configureNetwork, classifyNextRecord, setNetworkLearningMode)

from brainsquared.publishers.PikaPublisher import PikaPublisher
from brainsquared.subscribers.PikaSubscriber import PikaSubscriber

_ROUTING_KEY = "%s:%s:%s"

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)



class HTMClassifierModule(object):
  def __init__(self,
               user_id,
               device_type,
               rmq_address,
               rmq_user,
               rmq_pwd,
               input_metrics,
               output_metrics):

    """
    Motor Imagery Module.
    
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
    self.module_id = HTMClassifierModule.__name__

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
    self.categories = None
    self.network_config = None
    self.trained_network_path = None
    self.minval = None
    self.maxval = None

    # Module specific
    self._network = None
    

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


  def configure(self, categories, network_config, trained_network_path,
                minval, maxval):
    """Configure the module"""

    self._validate_metrics()

    self.categories = categories
    self.network_config = network_config
    self.trained_network_path = trained_network_path
    self.minval = minval
    self.maxval = maxval
    self.network_config["sensorRegionConfig"]["encoders"]["scalarEncoder"][
      "minval"] = minval

    # Init tag with first category
    self.last_tag["channel_0"] = self.categories[0]
    self.last_tag["timestamp"] = int(time.time() * 1000)


  def connect(self):
    """Initialize publisher and subscribers"""

    self.routing_keys = {
      self.input_metric: _ROUTING_KEY % (self.user_id, self.device_type,
                                         self.input_metric),
      self.output_metric: _ROUTING_KEY % (self.user_id, self.device_type,
                                          self.output_metric),
      self.tag_metric: _ROUTING_KEY % (self.user_id, self.device_type,
                                       self.tag_metric),
    }

    self.tag_subscriber = PikaSubscriber(self.rmq_address,
                                         self.rmq_user, self.rmq_pwd)
    self.classification_publisher = PikaPublisher(self.rmq_address,
                                                  self.rmq_user, self.rmq_pwd)
    self.input_metric_subscriber = PikaSubscriber(self.rmq_address,
                                                  self.rmq_user, self.rmq_pwd)
    self.output_metric_publisher = PikaPublisher(self.rmq_address,
                                                 self.rmq_user, self.rmq_pwd)

    self.tag_subscriber.connect()
    self.classification_publisher.connect()
    self.input_metric_subscriber.connect()
    self.output_metric_publisher.connect()

    self.tag_subscriber.subscribe(self.routing_keys[self.tag_metric])
    self.classification_publisher.register(self.routing_keys[self.tag_metric])
    self.input_metric_subscriber.subscribe(self.routing_keys[self.input_metric])
    self.output_metric_publisher.register(self.routing_keys[self.output_metric])


  def train(self, training_file, num_records):
    """Create a network and training it on a CSV data source"""

    dataSource = FileRecordStream(streamID=training_file)
    dataSource.setAutoRewind(True)
    self._network = configureNetwork(dataSource, self.network_config)
    for i in xrange(num_records):  # Equivalent to: network.run(num_records) 
      self._network.run(1)
    self._network.save(self.trained_network_path)


  def classify(self):
    """Get data from rabbitMQ and classify input data"""

    if self._network is None:
      self._network = Network(self.trained_network_path)

    regionNames = self._get_all_regions_names()
    setNetworkLearningMode(self._network, regionNames, False)
    _LOGGER.info("[Module %s] Starting Motor Imagery module. Routing keys: %s"
                 % (self.module_id, self.routing_keys))

    self.input_metric_subscriber.consume_messages(
        self.routing_keys[self.input_metric],
        self._tag_and_classify)


  def _get_all_regions_names(self):

    region_names = []
    for region_config_key, region_config in self.network_config.items():
      region_names.append(region_config["regionName"])

    return region_names


  def _tag_and_classify(self, ch, method, properties, body):
    """Tag data and runs it through the classifier"""

    self._update_last_tag()

    input_data = simplejson.loads(body)
    timestamp = input_data["timestamp"]

    if self.maxval is not None and self.minval is not None:
      value = np.clip(input_data["channel_0"], self.minval, self.maxval)
    else:
      value = input_data["channel_0"]

    classificationResults = classifyNextRecord(self._network,
                                               self.network_config,
                                               timestamp,
                                               value,
                                               self.last_tag["channel_0"])
    inferredCategory = classificationResults["bestInference"]
    _LOGGER.debug("Raw results: %s" % classificationResults)

    buffer = [{"timestamp": timestamp, "channel_0": inferredCategory}]

    self.output_metric_publisher.publish(self.routing_keys[self.output_metric],
                                         buffer)


  def _update_last_tag(self):
    """
    Consume all tags in the queue and keep the last one (i.e. the most up 
    to date)
    
    A tag is a dict with the following format:
     tag = {"timestamp": <int>, "channel_0": <float>}
    
    """
    while 1:
      (meth_frame, header_frame, body) = self.tag_subscriber.get_one_message(
          self.routing_keys[self.tag_metric])
      if body:
        self.last_tag = simplejson.loads(body)
      else:
        _LOGGER.info("Last tag: {}".format(self.last_tag))
        return
