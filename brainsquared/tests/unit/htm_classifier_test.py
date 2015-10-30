#!/usr/bin/env python
import simplejson as json
import unittest

from htmresearch.frameworks.classification.utils.network_config import \
  generateNetworkPartitions

from brainsquared.analytics.htm_classifier import HTMClassifier

_TRAIN_SET_SIZE = 2000
_NTWK_CONFIG = "config/network_config.json"
_TRAINING_DATA = "data/test_data.csv"



class HTMClassifierTest(unittest.TestCase):
  def setUp(self):
    self.network_config = None
    self.classifier = None
    with open(_NTWK_CONFIG, "rb") as jsonFile:
      self.network_config = json.load(jsonFile)


  def testTrainingAccuracy(self):
    partitions = generateNetworkPartitions(self.network_config, _TRAIN_SET_SIZE)
    training_sets = {"left": _TRAINING_DATA, "right": _TRAINING_DATA}

    self.classifier = HTMClassifier(training_sets, self.network_config,
                                    _TRAIN_SET_SIZE, partitions)

    self.classifier.initialize()
    training_accuracies = self.classifier.train()

    self.assertEqual(training_accuracies["left"],
                     94.75, "left classification accuracy is incorrect")
    self.assertEqual(training_accuracies["right"],
                     94.75, "right classification accuracy is incorrect")


    def testClassificationAccuracy(self):
      self.classifier.classify()


  if __name__ == "__main__":
    unittest.main()
