"""
Module to collect and tag training data and write them to a CSV.
"""
import csv
import logging
import numpy as np
from sklearn import svm
from sklearn.externals import joblib
import os

import brainsquared
from brainsquared.utils.metadata import get_num_channels
from brainsquared.modules.classifiers.SKLearnClassifier import (
  CLASSIFIER_PATH, VALID_CLASSIFIER_TYPES)

from brainsquared.modules.sinks.CSVWriterSink import TRAINING_DATA_PATH

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)



def train_classifier(device, metric, num_categories, classifier_type):
  categories = range(num_categories)
  num_channels = get_num_channels(device, metric)
  if classifier_type not in VALID_CLASSIFIER_TYPES:
    raise ValueError("Classifier type invalid (%s). Valid classifier types "
                     "are: %s" % (classifier_type, VALID_CLASSIFIER_TYPES))

  labels = []
  input_values = []
  for category in categories:
    input_file = TRAINING_DATA_PATH % {
      "tag": category,
      "metric": metric,
      "device": device
    }
    with open(input_file, "rb") as csvFile:
      reader = csv.reader(csvFile)
      headers = reader.next()

      for row in reader:
        data = dict(zip(headers, row))
        channel_values = []
        category = data["tag"]
        for i in range(num_channels):
          channel = "channel_%s" % i
          channel_values.append(float(data[channel]))
        input_values.append(channel_values)
        labels.append(category)

  num_records = len(input_values)
  num_train_records = num_records * 2 / 3
  train_input_values = input_values[:num_train_records]
  test_input_values = input_values[num_train_records:]
  train_labels = labels[:num_train_records]
  test_labels = labels[num_train_records:]

  X = np.array(train_input_values)
  y = np.array(train_labels)

  if classifier_type == "svm":
    clf = svm.LinearSVC()
  else:
    raise ValueError("Classifier type is '%s' but can only be: %s"
                     % VALID_CLASSIFIER_TYPES)

  clf.fit(X, y)

  X_test = np.array(test_input_values)
  y_test = np.array(test_labels)

  score = clf.score(X_test, y_test)

  classifier_path = CLASSIFIER_PATH % {
    "classifier_type": classifier_type,
    "device": device,
    "input_metric": metric
  }

  model_path = os.path.join(
      os.path.dirname(brainsquared.__file__), "module_runners", classifier_path)
  joblib.dump(clf, model_path)
  return classifier_path, score



if __name__ == "__main__":
  _DEVICE = "neurosky"
  _METRIC = "attention"
  _NUM_CATEGORIES = 2  # [0, 1]
  _CLASSIFIER_TYPE = "svm"

  clf_path, score = train_classifier(
      _DEVICE, _METRIC, _NUM_CATEGORIES, _CLASSIFIER_TYPE)
  print "Score: %s" % score
  
  # Only for the neurosky (making sure decision boundary of classifier is 
  # trivial for # attention)
  if _DEVICE == "neurosky" and _METRIC == "attention":
    clf2 = joblib.load(clf_path)
    print "== Neurosky attention =="
    print "Predict 70: %s" % clf2.predict([70])
    print "Predict 40: %s" % clf2.predict([40])
