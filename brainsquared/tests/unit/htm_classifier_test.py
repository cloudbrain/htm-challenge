#!/usr/bin/env python
import simplejson
import unittest

from htmresearch.frameworks.classification.utils.network_config import \
  generateNetworkPartitions

from brainsquared.analytics.htm_classifier import HTMClassifier

_TRAIN_SET_SIZE = 2000
_NTWK_CONFIG = "config/network_config.json"
_TRAINING_DATA = "data/test_data.csv"
_CATEGORIES = ["baseline", "left", "right"]


class HTMClassifierTest(unittest.TestCase):
  def setUp(self):
    with open(_NTWK_CONFIG, "rb") as jsonFile:
      self.network_config = simplejson.load(jsonFile)
    self.classifier = HTMClassifier(self.network_config, _TRAINING_DATA, 
                                    _CATEGORIES)
    self.classifier.initialize()

  def testTrainingAccuracy(self):
    partitions = generateNetworkPartitions(self.network_config, _TRAIN_SET_SIZE)
    training_accuracy = self.classifier.train(_TRAIN_SET_SIZE, partitions)
    self.assertEqual(training_accuracy, 94.75,
                     "classification accuracy is incorrect")


  def testClassificationAccuracy(self):
    mu = 7
    tag = "middle"
    result = self.classifier.classify(input_data=mu, target=tag, 
                                  learning_is_on=True)
    print "classification_result: %s" % result


if __name__ == "__main__":
  unittest.main()
