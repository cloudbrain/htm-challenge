#!/usr/bin/env python
import numpy
from nupic.data.file_record_stream import FileRecordStream

from htmresearch.frameworks.classification.classification_network import (
  configureNetwork, runNetwork)



class HTMClassifier(object):
  """HTM classifier for EEG data"""


  def __init__(self, network_config, training_set, categories):
    """
    Constructor.
    @param network_config: (dict) configuration of the classification network.
    @param training_set: (string) path to training set. 
    """

    self.network_config = network_config
    self.training_set = training_set
    self.network = None
    self.categories = categories


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

    return runNetwork(self.network,
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
    return self._process_one_record(self.network, input_data, target)


  def _process_one_record(self, network, input_data, target):

    sensorRegion = network.regions["sensor"]
    sensorRegion.setParameter("useDataSource", False)
    sensorRegion.setParameter("nextInput", input_data)

    if target not in self.categories:
      raise ValueError("%s is not in the list of "
                       "categories: %s" % (target, self.categories))
    else:
      category = self.categories.index(target)
      sensorRegion.setParameter("nextCategory", category)

    network.run(1)
    return _getClassifierInference(network)



def _disable_all_learning(network, learning_is_on):
  if learning_is_on:
    return
  else:
    raise NotImplementedError("Disabling all learning is not yet implemented")



def _getClassifierInference(network):
  """Return output categories from the classifier region."""

  classifierRegion = network.regions["classifier"]
  if classifierRegion.type == "py.KNNClassifierRegion":
    # The use of numpy.lexsort() here is to first sort by labelFreq, then
    # sort by random values; this breaks ties in a random manner.
    inferenceValues = classifierRegion.getOutputData("categoriesOut")
    randomValues = numpy.random.random(inferenceValues.size)
    return numpy.lexsort((randomValues, inferenceValues))[-1]

  elif classifierRegion.type == "py.CLAClassifierRegion":
    return classifierRegion.getOutputData("categoriesOut")[0]
