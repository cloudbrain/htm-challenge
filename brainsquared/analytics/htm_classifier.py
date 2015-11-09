#!/usr/bin/env python
from nupic.data.file_record_stream import FileRecordStream

from htmresearch.frameworks.classification.classification_network import (
  configureNetwork, trainNetwork)



class HTMClassifier(object):
  """HTM classifier for EEG data"""


  def __init__(self, network_config, training_set):
    """
    Constructor.
    @param network_config: (dict) configuration of the classification network.
    @param training_set: (string) path to training set. 
    """

    self.network_config = network_config
    self.training_set = training_set
    self.network = None


  def initialize(self):
    """Initialize classification networks for left and right electrodes."""

    data_source = FileRecordStream(streamID=self.training_set)
    self.network = configureNetwork(data_source,
                                    self.network_config)


  def train(self, training_set_size, partitions):
    """
    Train the HTM network
    @param training_set_size: size of the training set.
    @param partitions: (list of namedtuple) list of partitions to train the 
      network. E.g: 
      [Partition(partName=SP, index=0), ..., Partition(partName=test, index=0)]
    @return classification_accuracy: (float) classification accuracy, 0 to 100.

    """

    return trainNetwork(self.network,
                        self.network_config,
                        partitions,
                        training_set_size)


  def classify(self, input_data, target, learning_is_on=True):
    """ 
    Classify a data point and return the result. The learning can be on or off.
    @param input_data: (float) input data to classify
    @param target: target label
    @param learning_is_on: (Boolean) turn learning on or off.
    @return classification_results: classification results.
    """

    _disable_all_learning(self.network, learning_is_on)
    return _process_one_record(self.network, input_data, target)



def _process_one_record(network, input_data, target):
  # TODO / Note: update nupic region, or maybe create a new RecordSensorRegion
  sensorRegion = network.regions["sensor"]
  sensorRegion.setParameter("getNextRecord", True)
  sensorRegion.getSelf().compute()
  network.run(1)


def _disable_all_learning(network, learning_is_on):
  if learning_is_on:
    return 
  else:
    raise NotImplementedError("Disabling all learning is not yet implemented")
