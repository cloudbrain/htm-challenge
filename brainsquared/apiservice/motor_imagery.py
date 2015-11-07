import simplejson as json
import logging

from htmresearch.frameworks.classification.utils.network_config import \
  generateNetworkPartitions

from brainsquared.publishers.PikaPublisher import PikaPublisher
from brainsquared.subscribers.PikaSubscriber import PikaSubscriber

from brainsquared.analytics.htm_classifier import HTMClassifier

_LEARNING_IS_ON = True
_NETWORK_CONFIG = "config/network_config.json"
_TRAINING_DATA = "data/training_data.csv"
_TRAIN_SET_SIZE = 2000
_PRE_TRAIN = False
_ROUTING_KEY = "%s:%s:%s"

# metric names conventions
_MU = "mu"
_TAG = "tag"
_CLASSIFICATION = "classification"

# size of the data batch to take from a rabbitMQ queue
_LOGGER = logging.getLogger(__name__)

with open(_NETWORK_CONFIG, "rb") as jsonFile:
  network_config = json.load(jsonFile)
partitions = generateNetworkPartitions(network_config, _TRAIN_SET_SIZE)



class HTMMotorImageryModule(object):
  def __init__(self,
               user_id,
               module_id,
               device_type,
               rmq_address,
               rmq_user,
               rmq_pwd):
    self.module_id = module_id
    self.user_id = user_id
    self.rmq_address = rmq_address
    self.rmq_user = rmq_user
    self.rmq_pwd = rmq_pwd
    
    self.classification_publisher = None
    self.mu_subscriber = None
    self.tag_subscriber = None
    self.tag_publisher = None

    self.routing_keys = {
      "mu": _ROUTING_KEY % (user_id, device_type, _MU),
      "tag": _ROUTING_KEY % (user_id, module_id, _TAG),
      "classification": _ROUTING_KEY % (user_id, module_id, _CLASSIFICATION)
    }

    self.last_tag = None

  def initialize(self):
    """
    Initialize classifier, publisher (classification), and subscribers (mu 
    and tag)
    """
  
    classifier = HTMClassifier(network_config, _TRAINING_DATA)
    classifier.initialize()

    if _PRE_TRAIN:
      classifier.train(_TRAIN_SET_SIZE, partitions)


    self.tag_subscriber = PikaSubscriber(self.rmq_address,
                                         self.rmq_user, self.rmq_pwd)
    self.tag_publisher = PikaPublisher(self.rmq_address,
                                         self.rmq_user, self.rmq_pwd)
    self.mu_subscriber = PikaSubscriber(self.rmq_address,
                                        self.rmq_user, self.rmq_pwd)
    self.classification_publisher = PikaPublisher(self.rmq_address,
                                                  self.rmq_user, self.rmq_pwd)

    self.tag_subscriber.connect()
    self.tag_publisher.connect()
    self.mu_subscriber.connect()
    self.classification_publisher.connect()

    self.tag_subscriber.subscribe(self.routing_keys["tag"])
    self.tag_publisher.register(self.routing_keys["tag"])
    self.mu_subscriber.subscribe(self.routing_keys["mu"])
    self.classification_publisher.register(self.routing_keys["classification"])
    

  def start(self, logger):
    
    logger.info("[Module %s] Starting Motor Imagery module. Routing keys: %s" 
                % (self.module_id, self.routing_keys))

    def _callback(ch, method, properties, body):
      self.last_tag = self._update_last_tag(self.last_tag)
      logger.info("[Module %s] mu: %s | last_tag: %s" % (self.module_id, body, 
                                                        self.last_tag))

    
    self.mu_subscriber.consume_messages(self.routing_keys["mu"], _callback)


  def _update_last_tag(self, last_tag):
    while 1:
      (meth_frame, header_frame, body) = self.tag_subscriber.get_one_message(
        self.routing_keys["tag"])
      if body:
         last_tag = body
      else:
        return last_tag
    
    
  def _consume_messages(self, routing_key, buffer_size=1):
    """
    Get all items in the queue
    @return buffer: (list) list of points
    points). E.g:
      [
        {left: <float>, right: <float>}, .., {left: <float>, right: <float>},
        ...
        {left: <float>, right: <float>}, .., {left: <float>, right: <float>}
      ]
    """

    buffer = []
    while len(buffer) < buffer_size:
      (meth_frame, header_frame, body) = self.subscriber.get_one_message(
        routing_key)
      if body:
        buffer.append(json.loads(body))

    return buffer


  def _publish(self, data):
    self.publisher.publish(self.out_routing_key, data)


  def do_job(self, model, tag):
    """
    Get all buffers of data in the queue, tag and classify them, 
    and publish it back to RMQ.
    """

    buffer = self._consume_messages(self.in_routing_key, buffer_size=1)

    for datapoint in buffer:
      results = _tag_and_classify(datapoint, model, tag)
      self._publish(results)



def _tag_and_classify(data, model, best_tag):
  """
  Label a datapoint with the best tag and get classification 
  result.
  @return result: classification result
  """
  mu_left = data["left"]
  mu_right = data["right"]

  # combine tags with input data and classify 
  left_result = model["left"].classify(best_tag, mu_left,
                                       _LEARNING_IS_ON)
  right_result = model["right"].classify(best_tag, mu_right,
                                         _LEARNING_IS_ON)

  result = _reconcile_results(left_result, right_result, best_tag)
  return result



def _reconcile_results(left_result, right_result, best_tag):
  """
  
  @param left_result: result from the left electrode classification
  @param right_result: result from the right electrode classification
  @param best_tag: most common tag. Used if the two results disagree.
  @return: result after reconciliation of the two input results.
  """

  if left_result == right_result:
    return left_result
  else:
    return best_tag



def _get_best_tag(tags):
  """
  Extract the best tag from a list of tag. Here we take the mean of the tags 
  and consider it is the best value.
  @param tags: (list) tags from which with want to extract the bets tag value.
  @return last_tag: (float) best tag value.
  """
  return sum(tags) / max(len(tags), 1)
