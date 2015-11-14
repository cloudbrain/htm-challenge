# !/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
import shutil
import unittest
import csv

try:
  import simplejson as json
except ImportError:
  import json

from nupic.data.file_record_stream import FileRecordStream

from htmresearch.frameworks.classification.utils.sensor_data import \
  generateSensorData
from htmresearch.frameworks.classification.utils.network_config import \
  generateSampleNetworkConfig
from htmresearch.frameworks.classification.classification_network import \
  _getClassifierInference

from brainsquared.analytics.motor_imagery.htm_classifier import HTMClassifier

# Parameters to generate the artificial sensor data
OUTFILE_NAME = "white_noise"
SEQUENCE_LENGTH = 200
NUM_RECORDS = 2400
START_TEST = NUM_RECORDS * 3 / 4
WHITE_NOISE_AMPLITUDES = [0.0, 1.0]
SIGNAL_AMPLITUDES = [1.0]
SIGNAL_MEANS = [1.0]
SIGNAL_PERIODS = [20.0]

# Additional parameters to run the classification experiments 
RESULTS_DIR = "results"
MODEL_PARAMS_DIR = 'model_params'
DATA_DIR = "data"

# Classifier types
CLA_CLASSIFIER_TYPE = "py.CLAClassifierRegion"
KNN_CLASSIFIER_TYPE = "py.KNNClassifierRegion"

CATEGORIES = [1, 2]
NUM_CATEGORIES = len(CATEGORIES)



class TestSensorDataClassification(unittest.TestCase):
  """Test classification results for sensor data."""


  def setUp(self):
    with open("config/network_config.json", "rb") as jsonFile:
      self.templateNetworkConfig = json.load(jsonFile)


  def testClassificationAccuracy(self):
    """Test classification accuracy for sensor data."""

    networkConfigurations = generateSampleNetworkConfig(
      self.templateNetworkConfig, NUM_CATEGORIES)

    for networkConfig in networkConfigurations:
      for noiseAmplitude in WHITE_NOISE_AMPLITUDES:
        for signalMean in SIGNAL_MEANS:
          for signalAmplitude in SIGNAL_AMPLITUDES:
            for signalPeriod in SIGNAL_PERIODS:
              sensorType = networkConfig["sensorRegionConfig"].get(
                "regionType")
              spEnabled = networkConfig["sensorRegionConfig"].get(
                "regionEnabled")
              tmEnabled = networkConfig["tmRegionConfig"].get(
                "regionEnabled")
              upEnabled = networkConfig["tpRegionConfig"].get(
                "regionEnabled")
              classifierType = networkConfig["classifierRegionConfig"].get(
                "regionType")

              expParams = ("RUNNING EXPERIMENT WITH PARAMS:\n"
                           " * numRecords=%s\n"
                           " * signalAmplitude=%s\n"
                           " * signalMean=%s\n"
                           " * signalPeriod=%s\n"
                           " * noiseAmplitude=%s\n"
                           " * sensorType=%s\n"
                           " * spEnabled=%s\n"
                           " * tmEnabled=%s\n"
                           " * tpEnabled=%s\n"
                           " * classifierType=%s\n"
                           ) % (NUM_RECORDS,
                                signalAmplitude,
                                signalMean,
                                signalPeriod,
                                noiseAmplitude,
                                sensorType.split(".")[1],
                                spEnabled,
                                tmEnabled,
                                upEnabled,
                                classifierType.split(".")[1])
              print expParams

              inputFile = generateSensorData(DATA_DIR,
                                             OUTFILE_NAME,
                                             signalMean,
                                             signalPeriod,
                                             SEQUENCE_LENGTH,
                                             NUM_RECORDS,
                                             signalAmplitude,
                                             NUM_CATEGORIES,
                                             noiseAmplitude)
              
              inputFile="mu/right_test.csv"

              classifier = HTMClassifier(networkConfig, inputFile, CATEGORIES)
              minval, maxval = classifier.initialize()
              points = []
              
              classifier2 = HTMClassifier(networkConfig, inputFile, CATEGORIES)
              classifier2.initialize()
              net = classifier.network
              sensorRegion = net.regions["sensor"]
              classifierRegion = net.regions["classifier"]
              with open(inputFile, 'rb') as csvfile:
                reader = csv.reader(csvfile)
                reader.next()
                reader.next()
                reader.next()

                numCorrect = 0
                numCorrect2 = 0
                numRecords = 0

                for row in reader:
                  timestamp = row[0]
                  inputData = float(row[1])
                  points.append(inputData)
                  target = int(row[2])
                  result = classifier.classify(inputData, target,
                                               learning_is_on=False)
                  sensorRegion.setParameter("useDataSource", True)
                  net.run(1)
                  result2 = CATEGORIES[int(_getClassifierInference(
                    classifierRegion))]

                  if result2 != result:
                    print "numRecords = %s" % numRecords
                    print "target = %s" % target
                    print "result = %s" % result
                    print "result2 = %s" % result2
                  if int(result) == int(target):
                    if numRecords > START_TEST:
                      numCorrect += 1
                  if int(result2) == int(target):
                    if numRecords > START_TEST:
                      numCorrect2 += 1

                  numRecords += 1

              classificationAccuracy = round(100.0 * numCorrect / (
                numRecords - START_TEST), 2)
              classificationAccuracy2 = round(100.0 *
                                              numCorrect / (
                                                numRecords - START_TEST), 2)
              print classificationAccuracy
              print classificationAccuracy2
              
              import numpy as np
              bins = np.linspace(0, 1, 10)
              histogram = np.histogram(np.array(points), bins)

              if (noiseAmplitude == 0
                  and signalMean == 1.0
                  and signalAmplitude == 1.0
                  and signalPeriod == 20.0
                  and classifierType == KNN_CLASSIFIER_TYPE
                  and spEnabled
                  and tmEnabled
                  and not upEnabled):
                self.assertEqual(classificationAccuracy, 100.00)
              elif (noiseAmplitude == 0
                    and signalMean == 1.0
                    and signalAmplitude == 1.0
                    and signalPeriod == 20.0
                    and classifierType == CLA_CLASSIFIER_TYPE
                    and spEnabled
                    and tmEnabled
                    and not upEnabled):
                self.assertEqual(classificationAccuracy, 100.00)
              elif (noiseAmplitude == 0
                    and signalMean == 1.0
                    and signalAmplitude == 1.0
                    and signalPeriod == 20.0
                    and classifierType == CLA_CLASSIFIER_TYPE
                    and spEnabled
                    and not tmEnabled
                    and not upEnabled):
                self.assertEqual(classificationAccuracy, 100.00)
              elif (noiseAmplitude == 1.0
                    and signalMean == 1.0
                    and signalAmplitude == 1.0
                    and signalPeriod == 20.0
                    and classifierType == CLA_CLASSIFIER_TYPE
                    and spEnabled
                    and tmEnabled
                    and not upEnabled):
                # using AlmostEqual until the random bug issue is fixed
                self.assertAlmostEqual(classificationAccuracy, 80, delta=5)
              elif (noiseAmplitude == 1.0
                    and signalMean == 1.0
                    and signalAmplitude == 1.0
                    and signalPeriod == 20.0
                    and classifierType == CLA_CLASSIFIER_TYPE
                    and spEnabled
                    and not tmEnabled
                    and not upEnabled):
                # using AlmostEqual until the random bug issue is fixed
                self.assertAlmostEqual(classificationAccuracy, 81, delta=5)


  def tearDown(self):
    shutil.rmtree(DATA_DIR)



if __name__ == "__main__":
  unittest.main()
