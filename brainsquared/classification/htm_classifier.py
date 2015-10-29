#!/usr/bin/env python
import simplejson
from os.path import dirname, join

from nupic.data.file_record_stream import FileRecordStream

from htmresearch.frameworks.classification.classification_network import (
  configureNetwork,
  runNetwork)
from htmresearch.frameworks.classification.utils.network_config import (
  generateNetworkPartitions)


def train(trainingData):
  """ Run classification network on CSV data """
  
  # TODO: extract the actual number of records from the CSV file instead of 
  # using this hardcoded number.
  numRecords = 1000
  
  # assume that the network config file is in the same directory
  with open("network_config.json", "rb") as jsonFile:
    networkConfig = simplejson.load(jsonFile)


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

  expParams = ("RUNNING CLASSIFIER WITH PARAMS:\n"
               " * numRecords=%s\n"
               " * sensorType=%s\n"
               " * spEnabled=%s\n"
               " * tmEnabled=%s\n"
               " * tpEnabled=%s\n"
               " * classifierType=%s\n"
               ) % (numRecords,
                    sensorType.split(".")[1],
                    spEnabled,
                    tmEnabled,
                    upEnabled,
                    classifierType.split(".")[1])
  print expParams

  
  dataSource = FileRecordStream(streamID=trainingData)
  network = configureNetwork(dataSource,
                             networkConfig)
  
  # TODO: we might want to have a different type of parition (e.g. no test 
  # partition) 
  partitions = generateNetworkPartitions(networkConfig,
                                         numRecords)
  

  # TODO: split this method between test and train
  classificationAccuracy = runNetwork(network, networkConfig, partitions, 
                                    numRecords)
  
  return classificationAccuracy
  
  # TODO: persist model after training
  
  
def test():
  # TODO: load model from persisted after training
  pass

  # TODO: when getting data from rabbit and not a CSV file, publish test results
  # back to rabbitMQ
  # muleft = {"timestamp": , "raw": , "classification": , "class": }
  # muright = {"timestamp": , "raw": , "classification": , "class": }


if __name__ == "__main__":
  trainingData = join(dirname(dirname(__file__)), "data", "test_data.csv")
  train(trainingData)


