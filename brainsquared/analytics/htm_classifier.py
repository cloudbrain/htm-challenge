#!/usr/bin/env python
from nupic.data.file_record_stream import FileRecordStream

from htmresearch.frameworks.classification.classification_network import (
  configureNetwork, trainNetwork)



class HTMClassifier(object):
  """HTM classifier for EEG data"""


  def __init__(self, training_sets, network_config, training_set_size,
               partitions):
    """Constructor.
    @param training_sets: (dict) path to left and right training sets. 
      {"left": <path_to_csv>, "right": <path_to_csv>}
    @param network_config: (dict) configuration for let and right networks.
    @param training_set_size: size of the training set for both models.
    @param partitions: (list of namedtuple) list of partitions to train the 
      network. E.g: 
      [Partition(partName=SP, index=0), ..., Partition(partName=test, index=0)]
    """

    self.training_sets = training_sets
    self.training_set_size = training_set_size
    self.network_config = network_config
    self.partitions = partitions

    self.networks = {"left": None, "right": None}


  def initialize(self):
    """Initialize classification networks for left and right electrodes."""

    left_data_source = FileRecordStream(streamID=self.training_sets["left"])
    right_data_source = FileRecordStream(streamID=self.training_sets["left"])

    self.networks["left"] = configureNetwork(left_data_source,
                                             self.network_config)
    self.networks["right"] = configureNetwork(right_data_source,
                                              self.network_config)


  def train(self):
    """Train the HTM networks"""

    classif_accuracies = {}

    # train network handling data form the LEFT electrode
    classif_accuracies["left"] = trainNetwork(self.networks["left"],
                                              self.network_config,
                                              self.partitions,
                                              self.training_set_size)
    # train network handling data form the RIGHT electrode
    classif_accuracies["right"] = trainNetwork(self.networks["right"],
                                               self.network_config,
                                               self.partitions,
                                               self.training_set_size)

    return classif_accuracies


  def classify(self, input_data, target, learning_is_on=True):
    """ 
    Classify a data point and return the result. The learning can be on or off.
    @param input_data: (float) input data to classify
    @param target: target label
    @param learning_is_on: (Boolean) turn learning on or off.
    @return classification_results: classification results.
    """
    
    classification_result = None
    return classification_result
