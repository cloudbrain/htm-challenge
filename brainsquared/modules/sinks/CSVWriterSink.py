import csv
import json
import logging
import time
import sys
import os
from brainsquared.modules.sinks.SinkModuleAbstract import SinkModuleAbstract
from brainsquared.utils.metadata import get_num_channels

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

_DATA_DIR = "data"

if not os.path.exists(_DATA_DIR):
    os.makedirs(_DATA_DIR)
    
TRAINING_DATA_PATH = os.path.join(
    _DATA_DIR, "data-%(tag)s-%(device)s-%(metric)s.csv")



class CSVWriterSink(SinkModuleAbstract):
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
    Collect, tag data (optional) and write to a CSV file. 
    
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

    super(CSVWriterSink, self).__init__(user_id,
                                        device_type,
                                        rmq_address,
                                        rmq_user,
                                        rmq_pwd,
                                        input_metrics,
                                        output_metrics,
                                        module_id)

    self.num_input_channels = get_num_channels(device_type, self.input_metric)

    # Set when configure() is called.
    self.tag = None
    self.time_offset = None
    self.recording_time = None
    self.csv_writer = None

    # Module specific.
    self.start_time = int(time.time() * 1000)
    self.channels = ["channel_%s" % i for i in range(self.num_input_channels)]
    self.headers = ["timestamp"] + self.channels


  def configure(self, time_offset=0, recording_time=None, tag=None):
    """
    Configure the module
    """

    self.tag = tag
    self.time_offset = time_offset
    self.recording_time = recording_time

    if tag is not None:
      self.headers.append("tag")

    self.csv_writer = csv.writer(open(TRAINING_DATA_PATH % {
      "tag": tag,
      "metric": self.input_metric,
      "device": self.device_type
    }, "wb"))

    self.csv_writer.writerow(self.headers)


  def start(self):
    self._process(self._write_csv)


  def _process(self, data_processor):
    """
    Subscribe to one input (1:1 mapping to routing key) and process data.
    
    :param data_processor: function to process the data. 
    :type data_processor: Function that takes as input a list of dicts and 
      outputs a list of dicts. Input/output list of dicts must have the 
      following 
      format:  
       {"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>}
    """
    subscriber = self.subscribers[self.input_metric_key]
    routing_key_in = self.routing_keys[self.input_metric_key]


    def callback(ch, method, properties, body):
      """Callback function called by the subscriber. Processes the data and 
      publishes it back"""
      buffer_in = json.loads(body)  # input data buffered
      data_processor(buffer_in)


    subscriber.subscribe(routing_key_in, callback)
    _LOGGER.info("[Module %s] Classifier module started.\n Routing keys: %s"
                 % (self.module_id, self.routing_keys))


  def _write_csv(self, buffer_in):

    for data in buffer_in:

      now = int(time.time() * 1000)
      if now > self.time_offset:
        row = data.values()
        if self.tag is not None:
          row.append(self.tag)
        self.csv_writer.writerow(row)
        _LOGGER.debug("Wrote row: %s" % row)

      if self.recording_time is not None:
        if now > self.recording_time + self.start_time:
          sys.exit(1)
