from abc import ABCMeta, abstractmethod



class PublisherInterface(object):
  __metaclass__ = ABCMeta


  def __init__(self, host):
    self.host = host


  @abstractmethod
  def connect(self):
    """
    Abstract method
    """


  @abstractmethod
  def disconnect(self):
    """
    Abstract method
    """


  @abstractmethod
  def register(self, routing_key):
    """Abstract method"""


  @abstractmethod
  def publish(self, routing_key, data):
    """
    Abstract method
    """
