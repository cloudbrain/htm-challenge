import json
import pika

# size of the data batch to take from a rabbitMQ queue
_CHUNK_SIZE = 10
_LEARNING_IS_ON = True



class Worker(object):
  def __init__(self, input_metric="mu",
               output_metric="classification"):
    self.input_metric = input_metric
    self.output_metric = output_metric
    self.pika_connection = None


  def connect(self):
    self.pika_connection = pika.BaseConnection()


  def publish(self, user_id, metric_name, value):
    """
    Publish data to rabbit MQ
    @param user_id: 
    @param metric_name: 
    @param value: 
    @return:
    """
    queue_id = "%s:%s:%s" % (user_id, metric_name, value)
    # TODO: publish to pika
    print self.pika_connection


  def get_data(self, user_id, metric_name, chunk_size):
    """
    Get chunk of data
    @return:
    """
    data = []
    # TODO: get a chunk of data from RMQ. Pass _CHUNK_SIZE. 
    print self.pika_connection

    # TODO: data to return:
    # [{left: <float>, right: <float>}, .., {left: <float>, right: <float>}]
    return data


  def get_tags(self, chunk_size):
    """
    Get a chunk of tags from RMQ
    @return:
    """
    raise NotImplementedError("Getting tags from RabbitMQ is not implemented "
                              "yet. Please provide list of tags for now.")
    tags = []
    # WIP: Get tags from RMQ
    return tags


  def process_chunk(self, user_id, model, chunk_size=_CHUNK_SIZE, tags=None):
    """
    Get a chunk of data from the queue, tag it, classify it, and publish it 
    back to RMQ.
    """

    data_chunk = self.get_data(user_id, self.input_metric, chunk_size)
    if not tags:
      tags = self.get_tags(chunk_size)
    best_tag = _get_best_tag(tags)

    results = _tag_and_classify_chunk(data_chunk, model, best_tag)
    self.publish(user_id, self.output_metric, results)



def _tag_and_classify_chunk(data_chunk, model, best_tag):
  """
  Label a chunk of data with the best tag and get classification 
  result for each data point in the chunk.
  @return results: labels of all the data points in the chunk.
  """
  results = []
  for data in data_chunk:
    mu_left = data["left"]
    mu_right = data["right"]

    # combine tags with input data and classify 
    left_result = model["left"].classify(best_tag, mu_left,
                                         _LEARNING_IS_ON)
    right_result = model["right"].classify(best_tag, mu_right,
                                           _LEARNING_IS_ON)

    result = _reconcile_results(left_result, right_result, best_tag)
    results.append(result)

  return results



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
