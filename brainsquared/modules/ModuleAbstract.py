import json
import logging
import uuid

from abc import abstractmethod, ABCMeta

from brainsquared.publishers.PikaPublisher import PikaPublisher
from brainsquared.subscribers.PikaSubscriber import PikaSubscriber

_ROUTING_KEY = "%s:%s:%s"

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)



class ModuleAbstract:
  __metaclass__ = ABCMeta


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
    Module Interface.
    
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

    if module_id is not None:
      self.module_id = module_id
    else:
      self.module_id = "{}-{}".format(self.__class__.__name__, uuid.uuid4())

    self.user_id = user_id
    self.device_type = device_type
    self.rmq_address = rmq_address
    self.rmq_user = rmq_user
    self.rmq_pwd = rmq_pwd

    self.routing_keys = {}
    self.publishers = {}
    self.subscribers = {}

    # NOTE: Don't use self._input_metrics / self._output_metrics directly.
    # - They need to be validated with the _validate_metrics implementation of 
    #   the child class.
    # - Once they are validated, use the <ModuleType>Abstract class valid 
    #   metrics  to register subscribers / publishers.
    self._input_metrics = input_metrics
    self._output_metrics = output_metrics


  @abstractmethod
  def _validate_metrics(self):
    """
    Validate input and output metrics and initialize them accordingly.
  
    For example, for a ClassifierModule, the input and output metrics 
    should respect the following structure:
  
    input_metrics = {"metric_to_classify": <string>, "label_metric": <string>}
    output_metrics = {"result_metric": <string>}
    
    """
    raise NotImplementedError("You must inpement the metric validation logic "
                              "for this module.")


  @abstractmethod
  def configure(self, **kwargs):
    """Configure the module with module specific params."""
    raise NotImplementedError("You must implement the logic for module "
                              "configuration!")


  def connect(self):
    """
    Initialize routing keys, publisher, and subscriber
    """

    if self._input_metrics is not None:  # Sources have no input metrics

      for input_metric_key, input_metric_name in self._input_metrics.items():
        self.routing_keys[input_metric_key] = _ROUTING_KEY % (
          self.user_id, self.device_type, input_metric_name)

      for input_metric_key in self._input_metrics.keys():
        sub = PikaSubscriber(self.rmq_address, self.rmq_user, self.rmq_pwd)
        sub.connect()
        sub.register(self.routing_keys[input_metric_key])
        self.subscribers[input_metric_key] = sub

    if self._output_metrics is not None:  # Sinks have no input metrics

      for output_metric_key, output_metric_name in self._output_metrics.items():
        self.routing_keys[output_metric_key] = _ROUTING_KEY % (
          self.user_id, self.device_type, output_metric_name)

      for output_metric_key in self._output_metrics.keys():
        pub = PikaPublisher(self.rmq_address, self.rmq_user, self.rmq_pwd)
        pub.connect()
        pub.register(self.routing_keys[output_metric_key])
        self.publishers[output_metric_key] = pub


  @abstractmethod
  def start(self):
    raise NotImplementedError("You need to implement the logic to start the "
                              "module. Subscribe to input data, process it, "
                              "and publish it back.")
