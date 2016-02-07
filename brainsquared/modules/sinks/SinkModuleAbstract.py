import logging

from abc import abstractmethod, ABCMeta
from brainsquared.modules.ModuleAbstract import ModuleAbstract

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)



class SinkModuleAbstract(ModuleAbstract):
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
    Sink Module Interface.
    
    Metrics conventions:
    - Input data: {"timestamp": <int>, "channel_0": <float>, ..., 
      "channel_N": <float>}
    
    
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

    super(SinkModuleAbstract, self).__init__(user_id,
                                             device_type,
                                             rmq_address,
                                             rmq_user,
                                             rmq_pwd,
                                             input_metrics,
                                             output_metrics,
                                             module_id)

    # Keeping track of input/output metrics and their keys
    self.input_metric = None
    self.input_metric_key = "input"

    self._validate_metrics()


  def _validate_metrics(self):
    """Validate input and output metrics and initialize them accordingly."""

    if self.input_metric_key in self._input_metrics:
      self.input_metric = self._input_metrics[self.input_metric_key]
    else:
      raise KeyError("The input metric '%s' is not set!"
                     % self.input_metric_key)

    if self._output_metrics is not None:
      raise ValueError("Sink do not accept out put metrics. Value should be "
                       "None but is %s" % self._output_metrics)
