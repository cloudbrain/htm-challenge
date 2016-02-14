import csv
import simplejson

from nupic.data.file_record_stream import FileRecordStream
from htmresearch.frameworks.classification.classification_network import (
  configureNetwork, classifyNextRecord, setNetworkLearningMode)

_NUM_CATEGORIES = 2
_NUM_RECORDS = 4730
_DATA_DIR = "backup"
_DEVICE = "neurosky"
_METRIC = "attention"

_MODEL_NAME = "htm-%(device)s-%(metric)s.nta" % {
  "device": _DEVICE, "metric": _METRIC}

_INPUT_FILES = ["%s/training-data-%s-%s.csv" % (_DATA_DIR, i, _METRIC)
                for i in range(_NUM_CATEGORIES)]

_CONFIG_JSON = "config/sensor_data_network_config.json"

_CONFIG = simplejson.load(open(_CONFIG_JSON, "rb"))

_REGION_CONFIG_KEYS = ("spRegionConfig", "tmRegionConfig",
                       "tpRegionConfig",
                       "classifierRegionConfig")

_REGION_NAMES = []
for region in _REGION_CONFIG_KEYS:
  if _CONFIG[region].get("regionEnabled"):
    _REGION_NAMES.append(_CONFIG[region]["regionName"])

if __name__ == "__main__":

  dataSource = FileRecordStream(streamID="backup/training-data-attention.csv")
  network = configureNetwork(dataSource, _CONFIG)
  setNetworkLearningMode(network, _REGION_NAMES, True)

  sensorRegion = network.regions[
  _CONFIG["sensorRegionConfig"].get("regionName")]
  classifierRegion = network.regions[
  _CONFIG["classifierRegionConfig"].get("regionName")]

  headers = ["x", "y", "label"]

  num_correct = 0
  for category in range(_NUM_CATEGORIES):
    csvFile = open(_INPUT_FILES[category], "rb")
    reader = csv.reader(csvFile)
    # skip 3 header rows
    reader.next()
    reader.next()
    reader.next()

    for row in reader:
      data = dict(zip(headers, row))
      x = int(data["x"]) / 1000000  # s
      y = float(data["y"])
      label = int(category)
      classificationResults = classifyNextRecord(network, _CONFIG, x, y, label)
      inferredCategory = classificationResults["bestInference"]

      print "Actual: %s | Predicted: %s " % (category,
                                             inferredCategory)
      if int(inferredCategory) == int(category):
        num_correct += 1

  print "ACCURACY: %s " % (float(num_correct) / (_NUM_RECORDS * 
                                                 _NUM_CATEGORIES))

  print "Serializing model to: %s" % _MODEL_NAME
  setNetworkLearningMode(network, _REGION_NAMES, False)
  network.save(_MODEL_NAME)
  
  print "Predict 40: %s" % classifyNextRecord(network, _CONFIG, -1, 40, -1)
  print "Predict 70: %s" % classifyNextRecord(network, _CONFIG, -1, 70, -1)
